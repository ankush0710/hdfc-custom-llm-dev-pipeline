"""
ml-service/app/services/training_worker.py

Dedicated ML background worker for executing SFTTrainer LoRA fine-tuning.
Persists real step progress, training loss, learning rate, and telemetry directly to Neon PostgreSQL.
"""
import json
import logging
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import (
    DATABASE_URL,
    HF_DATASET_REPO,
    HF_LOCAL_TEMP_DIR,
    HF_MODEL_REPO,
    HF_TOKEN,
    HF_UPLOAD_TIMEOUT_SECONDS,
)
from ..core.db import SessionLocal

logger = logging.getLogger(__name__)

# Active training cancellation events mapped by run_id
_ACTIVE_TRAINING_EVENTS: Dict[int, threading.Event] = {}


def request_stop_training(run_id: int) -> bool:
    """Trigger cancellation for an active training run."""
    event = _ACTIVE_TRAINING_EVENTS.get(run_id)
    if event:
        event.set()
        logger.info("Cancellation event set for run %d in ML worker.", run_id)
        return True
    return False


def execute_training_job_async(
    run_id: int,
    base_model: str,
    dataset_version_id: int,
    epochs: float,
    learning_rate: float,
    batch_size: int,
    training_method: str = "lora",
) -> None:
    """Launch asynchronous training thread so HTTP request returns immediately."""
    thread = threading.Thread(
        target=_run_training_worker_thread,
        kwargs={
            "run_id": run_id,
            "base_model": base_model,
            "dataset_version_id": dataset_version_id,
            "epochs": epochs,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "training_method": training_method,
        },
        daemon=True,
    )
    thread.start()
    logger.info("Training worker thread started for run %d.", run_id)


def _run_training_worker_thread(
    run_id: int,
    base_model: str,
    dataset_version_id: int,
    epochs: float,
    learning_rate: float,
    batch_size: int,
    training_method: str = "lora",
) -> None:
    """Worker function executing in background thread."""
    from ai.training.config import TrainingConfig
    from ai.training.model import prepare_model
    from ai.training.trainer import train_model, TrainingProgressCallback
    from huggingface_hub import HfApi

    stop_event = threading.Event()
    _ACTIVE_TRAINING_EVENTS[run_id] = stop_event

    db = None
    output_dir = str(Path(HF_LOCAL_TEMP_DIR) / "runs" / f"run_{run_id}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        # 1. Neon DB Lookup
        if SessionLocal:
            db = SessionLocal()

        ds_path = None
        if db:
            # Query dataset version file path
            from sqlalchemy import text
            row = db.execute(
                text("SELECT file_path, huggingface_path, version FROM dataset_versions WHERE id = :id"),
                {"id": dataset_version_id},
            ).fetchone()
            if row:
                raw_path = row[0]
                hf_path = row[1]
                if raw_path and os.path.exists(raw_path):
                    ds_path = raw_path
                elif hf_path and HF_TOKEN:
                    from huggingface_hub import hf_hub_download
                    ds_path = hf_hub_download(
                        repo_id=HF_DATASET_REPO,
                        filename=hf_path,
                        repo_type="dataset",
                        token=HF_TOKEN,
                    )
                elif raw_path:
                    ds_path = str(Path(raw_path).resolve())

            # Mark job as RUNNING in Neon
            db.execute(
                text("UPDATE training_run SET status = 'RUNNING', started_at = :now WHERE id = :id"),
                {"id": run_id, "now": datetime.utcnow()},
            )
            db.execute(
                text("UPDATE training_job SET status = 'RUNNING', started_at = :now, progress = 10 WHERE training_run_id = :id"),
                {"id": run_id, "now": datetime.utcnow()},
            )
            db.commit()

        if not ds_path or not os.path.exists(ds_path):
            raise FileNotFoundError(f"Dataset file could not be resolved or downloaded for version ID {dataset_version_id}")

        # 2. Callbacks for progress & cancellation
        def _should_stop() -> bool:
            if stop_event.is_set():
                return True
            if SessionLocal:
                try:
                    with SessionLocal() as check_db:
                        from sqlalchemy import text
                        res = check_db.execute(
                            text("SELECT status FROM training_run WHERE id = :id"),
                            {"id": run_id},
                        ).fetchone()
                        if res and str(res[0]).upper() in {"STOPPED", "CANCELLED"}:
                            return True
                except Exception:
                    pass
            return False

        def _on_step_progress(pct: int, step: int, max_steps: int, loss: Optional[float] = None, lr: Optional[float] = None):
            logger.info("ML WORKER CALLBACK: run_id=%d, pct=%d, step=%d/%d, loss=%s, lr=%s", run_id, pct, step, max_steps, loss, lr)
            if not SessionLocal:
                return

            try:
                with SessionLocal() as progress_db:
                    from sqlalchemy import text
                    safe_progress = max(0, min(99, int(pct)))
                    
                    # Fetch existing log_entries
                    job_row = progress_db.execute(
                        text("SELECT id, progress, log_entries FROM training_job WHERE training_run_id = :id ORDER BY id DESC LIMIT 1"),
                        {"id": run_id},
                    ).fetchone()

                    existing_entries = []
                    if job_row:
                        job_id = job_row[0]
                        prev_prog = job_row[1] or 0
                        if safe_progress < prev_prog:
                            safe_progress = prev_prog
                        try:
                            existing_entries = json.loads(job_row[2] or "[]")
                        except Exception:
                            existing_entries = []

                        entry = {
                            "step": step,
                            "pct": safe_progress,
                            "loss": round(float(loss), 6) if loss is not None else None,
                            "lr": round(float(lr), 8) if lr is not None else None,
                            "ts": datetime.utcnow().isoformat(),
                        }
                        existing_entries.append(entry)
                        if len(existing_entries) > 500:
                            existing_entries = existing_entries[-500:]

                        progress_db.execute(
                            text("""
                                UPDATE training_job
                                SET progress = :prog, status = 'RUNNING',
                                    current_step = :step, max_steps = :max_s,
                                    train_loss = :loss, current_lr = :lr,
                                    log_entries = :logs
                                WHERE id = :jid
                            """),
                            {
                                "prog": safe_progress,
                                "step": step,
                                "max_s": max_steps,
                                "loss": round(float(loss), 6) if loss is not None else None,
                                "lr": round(float(lr), 8) if lr is not None else None,
                                "logs": json.dumps(existing_entries),
                                "jid": job_id,
                            },
                        )
                        progress_db.commit()
            except Exception as prog_err:
                logger.warning("Failed to save progress update for run %d: %s", run_id, prog_err)

        # 3. Execute Model Training
        from app.ai.training_adapter.training_adapter import AITrainingAdapter
        train_result = AITrainingAdapter.train(
            base_model=base_model,
            dataset_path=ds_path,
            output_dir=output_dir,
            epochs=epochs,
            learning_rate=learning_rate,
            batch_size=batch_size,
            progress_callback=_on_step_progress,
            should_stop_callback=_should_stop,
        )

        # 4. Check if cancelled
        if _should_stop():
            logger.info("Training run %d was stopped by user request.", run_id)
            if SessionLocal:
                with SessionLocal() as final_db:
                    from sqlalchemy import text
                    final_db.execute(text("UPDATE training_run SET status = 'CANCELLED', completed_at = :now WHERE id = :id"), {"id": run_id, "now": datetime.utcnow()})
                    final_db.execute(text("UPDATE training_job SET status = 'CANCELLED', completed_at = :now WHERE training_run_id = :id"), {"id": run_id, "now": datetime.utcnow()})
                    final_db.commit()
            return

        # 5. Hugging Face Upload & Model Registration
        hf_model_path = None
        if HF_TOKEN:
            try:
                from huggingface_hub import HfApi
                api = HfApi(token=HF_TOKEN)
                clean_name = base_model.split("/")[-1].lower().replace(".", "_").replace("-", "_")
                hf_folder = f"models/hdfc_{clean_name}_run_{run_id}/v1.{run_id}.0"
                api.upload_folder(
                    folder_path=output_dir,
                    path_in_repo=hf_folder,
                    repo_id=HF_MODEL_REPO,
                    repo_type="model",
                )
                hf_model_path = hf_folder
                logger.info("Uploaded trained model for run %d to HF: %s", run_id, hf_folder)
            except Exception as up_err:
                logger.warning("HF model upload failed for run %d: %s", run_id, up_err)

        # 6. Mark COMPLETED in Neon DB and register in Model Registry
        if SessionLocal:
            with SessionLocal() as final_db:
                from sqlalchemy import text
                final_db.execute(
                    text("UPDATE training_run SET status = 'COMPLETED', completed_at = :now WHERE id = :id"),
                    {"id": run_id, "now": datetime.utcnow()},
                )
                final_db.execute(
                    text("UPDATE training_job SET status = 'COMPLETED', progress = 100, completed_at = :now WHERE training_run_id = :id"),
                    {"id": run_id, "now": datetime.utcnow()},
                )

                # Register model
                job_id_row = final_db.execute(
                    text("SELECT id FROM training_job WHERE training_run_id = :id ORDER BY id DESC LIMIT 1"),
                    {"id": run_id},
                ).fetchone()
                job_id = job_id_row[0] if job_id_row else None

                model_name = f"HDFC-{base_model.split('/')[-1]}-Run{run_id}"
                final_db.execute(
                    text("""
                        INSERT INTO model_registry (model_name, version, base_model, adapter_path, huggingface_path, status, training_job_id, created_at, updated_at)
                        VALUES (:name, :ver, :base, :adapter, :hf, 'READY', :jid, :now, :now)
                    """),
                    {
                        "name": model_name,
                        "ver": f"1.{run_id}.0",
                        "base": base_model,
                        "adapter": output_dir,
                        "hf": hf_model_path,
                        "jid": job_id,
                        "now": datetime.utcnow(),
                    },
                )
                final_db.commit()
                logger.info("Training run %d COMPLETED and registered successfully.", run_id)

    except Exception as exc:
        logger.exception("Training worker thread failed for run %d: %s", run_id, exc)
        if SessionLocal:
            try:
                with SessionLocal() as err_db:
                    from sqlalchemy import text
                    err_db.execute(
                        text("UPDATE training_run SET status = 'FAILED', error_message = :err, completed_at = :now WHERE id = :id"),
                        {"id": run_id, "err": str(exc), "now": datetime.utcnow()},
                    )
                    err_db.execute(
                        text("UPDATE training_job SET status = 'FAILED', error_message = :err, completed_at = :now WHERE training_run_id = :id"),
                        {"id": run_id, "err": str(exc), "now": datetime.utcnow()},
                    )
                    err_db.commit()
            except Exception as db_err:
                logger.error("Failed to update FAILED status in DB for run %d: %s", run_id, db_err)
    finally:
        _ACTIVE_TRAINING_EVENTS.pop(run_id, None)
        if db:
            db.close()
