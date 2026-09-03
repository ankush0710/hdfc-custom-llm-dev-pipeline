"""
ml-service/app/services/evaluation_worker.py

Dedicated background worker for executing model evaluation benchmarks.
Runs inference across test datasets, calculates accuracy/F1/latency, and persists results to Neon PostgreSQL.
"""
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.config import (
    DATABASE_URL,
    HF_DATASET_REPO,
    HF_LOCAL_TEMP_DIR,
    HF_TOKEN,
)
from ..core.db import SessionLocal

logger = logging.getLogger(__name__)

_ACTIVE_EVALUATION_EVENTS: Dict[int, threading.Event] = {}


def request_stop_evaluation(evaluation_id: int) -> bool:
    """Trigger cancellation for an active evaluation run."""
    event = _ACTIVE_EVALUATION_EVENTS.get(evaluation_id)
    if event:
        event.set()
        logger.info("Cancellation event set for evaluation %d.", evaluation_id)
        return True
    return False


def execute_evaluation_job_async(
    evaluation_id: int,
    run_id: int,
    model_id: int,
    test_dataset_id: int,
) -> None:
    """Launch asynchronous evaluation thread so HTTP request returns immediately."""
    thread = threading.Thread(
        target=_run_evaluation_worker_thread,
        kwargs={
            "evaluation_id": evaluation_id,
            "run_id": run_id,
            "model_id": model_id,
            "test_dataset_id": test_dataset_id,
        },
        daemon=True,
    )
    thread.start()
    logger.info("Evaluation worker thread started for evaluation %d.", evaluation_id)


def _run_evaluation_worker_thread(
    evaluation_id: int,
    run_id: int,
    model_id: int,
    test_dataset_id: int,
) -> None:
    stop_event = threading.Event()
    _ACTIVE_EVALUATION_EVENTS[evaluation_id] = stop_event

    db = None
    try:
        if SessionLocal:
            db = SessionLocal()

        base_model = "Qwen/Qwen3-0.6B"
        adapter_path = None
        resolved_test = None

        if db:
            from sqlalchemy import text
            # 1. Update status to RUNNING
            db.execute(
                text("UPDATE evaluation SET evaluation_status = 'RUNNING', started_at = :now WHERE evaluation_id = :id"),
                {"id": evaluation_id, "now": datetime.now(timezone.utc)},
            )
            db.commit()

            # 2. Get Model Info
            model_row = db.execute(
                text("SELECT base_model, adapter_path, huggingface_path FROM model_registry WHERE id = :id"),
                {"id": model_id},
            ).fetchone()
            if model_row:
                base_model = model_row[0] or base_model
                raw_adapter = model_row[1]
                hf_model = model_row[2]
                if raw_adapter and Path(raw_adapter).exists():
                    adapter_path = str(Path(raw_adapter).resolve())
                elif hf_model and HF_TOKEN:
                    from huggingface_hub import snapshot_download
                    adapter_path = str(snapshot_download(repo_id="ankush0710/hdfc-llm-models", allow_patterns=f"{hf_model}/*", token=HF_TOKEN))
                elif raw_adapter:
                    adapter_path = str(raw_adapter)

            # 3. Get Test Dataset Info
            ds_row = db.execute(
                text("SELECT file_path, huggingface_path FROM dataset_versions WHERE id = :id"),
                {"id": test_dataset_id},
            ).fetchone()
            if ds_row:
                raw_ds = ds_row[0]
                hf_ds = ds_row[1]
                if raw_ds and Path(raw_ds).exists():
                    resolved_test = str(Path(raw_ds).resolve())
                elif hf_ds and HF_TOKEN:
                    from huggingface_hub import hf_hub_download
                    resolved_test = str(hf_hub_download(repo_id=HF_DATASET_REPO, filename=hf_ds, repo_type="dataset", token=HF_TOKEN))
                elif raw_ds:
                    resolved_test = str(raw_ds)

        if not resolved_test or not Path(resolved_test).exists():
            raise FileNotFoundError(f"Test dataset file could not be resolved for dataset version ID {test_dataset_id}")

        # Run evaluation benchmark
        from app.ai.evaluation_adapter.evaluation_adapter import AIEvaluationAdapter
        eval_result = AIEvaluationAdapter.evaluate(
            evaluation_id=evaluation_id,
            base_model=base_model,
            adapter_path=adapter_path,
            test_dataset_path=resolved_test,
        )

        # Write completed metrics to Neon PostgreSQL
        if db:
            from sqlalchemy import text
            db.execute(
                text("""
                    UPDATE evaluation
                    SET evaluation_status = 'COMPLETED',
                        completed_at = :now,
                        total_examples = :total,
                        normalized_exact_match = :em,
                        answer_accuracy = :acc,
                        intent_structured_accuracy = :intent_acc,
                        token_precision = :prec,
                        token_recall = :rec,
                        token_f1 = :f1,
                        average_latency_seconds = :lat,
                        infrastructure_errors = :errs
                    WHERE evaluation_id = :id
                """),
                {
                    "now": datetime.now(timezone.utc),
                    "total": eval_result.total_examples,
                    "em": eval_result.normalized_exact_match,
                    "acc": eval_result.answer_accuracy,
                    "intent_acc": eval_result.intent_structured_accuracy,
                    "prec": eval_result.token_precision,
                    "rec": eval_result.token_recall,
                    "f1": eval_result.token_f1,
                    "lat": eval_result.average_latency_seconds,
                    "errs": eval_result.infrastructure_errors,
                    "id": evaluation_id,
                },
            )
            # Update Model Registry status to EVALUATED
            db.execute(
                text("UPDATE model_registry SET status = 'EVALUATED' WHERE id = :id"),
                {"id": model_id},
            )
            db.commit()
            logger.info("Evaluation %d COMPLETED and recorded in DB.", evaluation_id)

    except Exception as exc:
        logger.exception("Evaluation worker failed for evaluation %d: %s", evaluation_id, exc)
        if db:
            try:
                from sqlalchemy import text
                db.execute(
                    text("UPDATE evaluation SET evaluation_status = 'FAILED', error_message = :err, completed_at = :now WHERE evaluation_id = :id"),
                    {"err": str(exc), "now": datetime.now(timezone.utc), "id": evaluation_id},
                )
                db.commit()
            except Exception as db_err:
                logger.error("Failed to record evaluation failure in DB: %s", db_err)
    finally:
        _ACTIVE_EVALUATION_EVENTS.pop(evaluation_id, None)
        if db:
            db.close()
