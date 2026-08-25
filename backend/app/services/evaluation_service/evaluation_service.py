import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.dbConfig.database_config import SessionLocal
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.evaluation_run_model import Evaluation_Model
from app.model.model_registry import Model_Registry
from app.model.training_model import Training_Model
from app.processor.validator import resolve_file_path
from app.schema.evaluation_schema.evaluation_schema import EvaluationCreate, EvaluationResult

logger = logging.getLogger(__name__)


# ================================ create the evaluation runs ====================================== #
def create_evaluation(db: Session, payload: EvaluationCreate):
    # --- Guard 1: training run must exist and be COMPLETED ---
    training_run = db.query(Training_Model).filter(Training_Model.id == payload.run_id).first()
    if not training_run:
        raise ValueError(f"Training run with id {payload.run_id} not found")
    if training_run.status != "COMPLETED":
        raise ValueError(
            f"Training run {payload.run_id} is not COMPLETED (current status: '{training_run.status}'). "
            f"You can only evaluate a model after training has successfully completed."
        )

    # --- Guard 2: model must exist in Model Registry ---
    model = db.query(Model_Registry).filter(Model_Registry.id == payload.model_id).first()
    if not model:
        raise ValueError(
            f"Model with id {payload.model_id} not found in Model Registry. "
            f"Please register a model before creating an evaluation."
        )

    # --- Guard 3: test dataset version must exist ---
    dataset_version = db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == payload.test_dataset_id).first()
    if not dataset_version:
        raise ValueError(f"Dataset version with id {payload.test_dataset_id} not found")

    evaluation = Evaluation_Model(
        run_id=payload.run_id,
        model_id=payload.model_id,
        test_dataset_id=payload.test_dataset_id,
        evaluation_status="QUEUED"
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


# ================================ get the evaluation run by id ====================================== #
def get_evaluation_by_id(db: Session, evaluation_id: int):
    return (
        db.query(Evaluation_Model)
        .filter(Evaluation_Model.evaluation_id == evaluation_id)
        .first()
    )


# ======================= To list of all evaluation runs -> running, queued, completed, failed ================================== #
def list_evaluation(db: Session, run_id: int | None = None):
    query = db.query(Evaluation_Model)
    if run_id is not None:
        query = query.filter(Evaluation_Model.run_id == run_id)
    return query.order_by(Evaluation_Model.created_at.desc()).all()


# ================================ evaluation background worker ==================================== #
def _execute_evaluation_worker(evaluation_id: int):
    """Background worker executing real AI evaluation on the model and recording metrics."""
    db = SessionLocal()
    try:
        evaluation = db.query(Evaluation_Model).filter(Evaluation_Model.evaluation_id == evaluation_id).first()
        if not evaluation:
            logger.error("Evaluation %d not found in worker.", evaluation_id)
            return

        model = db.query(Model_Registry).filter(Model_Registry.id == evaluation.model_id).first()
        dataset_version = db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == evaluation.test_dataset_id).first()

        base_model = model.base_model if model and model.base_model else "Qwen/Qwen3-0.6B"

        # --- BUG 3 FIX: robust adapter path resolution ---
        # Priority: DB adapter_path (resolved) → full_training fallback (resolved)
        raw_adapter_path = model.adapter_path if model and model.adapter_path else None
        adapter_path = None

        if raw_adapter_path:
            resolved = Path(raw_adapter_path).resolve()
            if resolved.exists():
                adapter_path = str(resolved)
            else:
                logger.warning(
                    "Adapter path from DB '%s' (resolved: '%s') does not exist. "
                    "Falling back to full_training adapter.",
                    raw_adapter_path, resolved,
                )

        if adapter_path is None:
            fallback = (Path(__file__).resolve().parents[4] / "ai" / "artifacts" / "full_training")
            if fallback.exists():
                adapter_path = str(fallback)
                logger.info("Using fallback adapter path: %s", adapter_path)
            else:
                raise FileNotFoundError(
                    f"No valid adapter found. DB path '{raw_adapter_path}' missing, "
                    f"and fallback '{fallback}' also missing."
                )

        # Resolve test file path
        test_file = dataset_version.file_path if dataset_version else "data/hdfc_llm_test.jsonl"
        resolved_test = resolve_file_path(test_file)

        # If the resolved test file still doesn't exist, use bundled fallback
        if not os.path.exists(resolved_test):
            project_root = Path(__file__).resolve().parents[4]
            fallback_test = project_root / "data" / "hdfc_llm_test.jsonl"
            if fallback_test.exists():
                resolved_test = str(fallback_test)
                logger.warning(
                    "Test dataset file '%s' not found. Using fallback: %s",
                    test_file, resolved_test,
                )

        out_dir = Path(__file__).resolve().parents[4] / "ai" / "artifacts" / "evaluation" / f"eval_{evaluation_id}"

        logger.info(
            "Running AI evaluation for ID %d | model='%s' | adapter='%s' | test='%s'",
            evaluation_id, base_model, adapter_path, resolved_test,
        )

        from app.ai.evaluation_adapter.evaluation_adapter import AIEvaluationAdapter

        summary = AIEvaluationAdapter.evaluate(
            base_model=base_model,
            adapter_path=adapter_path,
            test_file=resolved_test,
            limit=5,
            output_dir=out_dir,
        )

        # Save actual computed AI metrics to PostgreSQL
        now = datetime.now(timezone.utc)
        evaluation.total_examples = summary["overall"]["total_examples"]
        evaluation.intent_json_validity = summary["intent"]["intent_json_validity"]
        evaluation.intent_structured_accuracy = summary["intent"]["intent_structured_accuracy"]
        evaluation.answer_accuracy = summary["structured_generation"]["answer_accuracy"]
        evaluation.citation_accuracy = summary["structured_generation"]["citation_accuracy"]
        evaluation.policy_flag_accuracy = summary["structured_generation"]["policy_flag_accuracy"]
        evaluation.escalation_accuracy = summary["structured_generation"]["escalation_accuracy"]
        evaluation.full_structured_match = summary["structured_generation"]["full_structured_match"]
        evaluation.normalized_exact_match = summary["free_form"]["normalized_exact_match"]
        evaluation.critical_safety_failures = summary["security"]["critical_safety_failures"]
        evaluation.infrastructure_errors = summary["infrastructure"]["infrastructure_errors"]
        evaluation.average_latency_seconds = summary["overall"]["average_latency_seconds"]
        evaluation.evaluation_status = "COMPLETED"
        evaluation.completed_at = now

        # Link evaluation result back to Model Registry and promote status
        if model and not model.evaluation_id:
            model.evaluation_id = evaluation.evaluation_id
            if model.status in {"TRAINED", "CREATED", "READY"}:
                model.status = "EVALUATED"

        db.commit()
        logger.info("Evaluation %d finished successfully — metrics saved to DB.", evaluation_id)

    except Exception as exc:
        logger.exception("Evaluation %d failed: %s", evaluation_id, exc)
        try:
            eval_record = db.query(Evaluation_Model).filter(Evaluation_Model.evaluation_id == evaluation_id).first()
            if eval_record:
                eval_record.evaluation_status = "FAILED"
                eval_record.error_message = str(exc)
                eval_record.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as rollback_err:
            logger.error("Failed to commit evaluation failure state: %s", rollback_err)
    finally:
        db.close()


# =========================== To start the evaluation run ================================== #
def start_evaluation(db: Session, evaluation_id: int, background_tasks: Optional[BackgroundTasks] = None):
    evaluation = get_evaluation_by_id(db, evaluation_id)

    if not evaluation:
        raise ValueError("Evaluation not found")

    if evaluation.evaluation_status == "COMPLETED":
        raise ValueError("Evaluation is already completed")

    if evaluation.evaluation_status == "RUNNING":
        raise ValueError(
            f"Evaluation {evaluation_id} is already running. "
            "Wait for it to complete before retrying."
        )
    evaluation.evaluation_status = "RUNNING"
    evaluation.started_at = datetime.now(timezone.utc)
    evaluation.error_message = None
    db.commit()
    db.refresh(evaluation)

    if background_tasks is not None:
        background_tasks.add_task(_execute_evaluation_worker, evaluation_id)
    else:
        thread = threading.Thread(target=_execute_evaluation_worker, args=(evaluation_id,), daemon=True)
        thread.start()

    return evaluation


# =========================== To save the evaluation metrics after run ================================== #
def save_evaluation_result(db: Session, evaluation_id: int, result: EvaluationResult):
    evaluation = get_evaluation_by_id(db, evaluation_id)

    if not evaluation:
        raise ValueError("Evaluation not found")

    evaluation.total_examples = result.total_examples
    evaluation.intent_json_validity = result.intent_json_validity
    evaluation.intent_structured_accuracy = result.intent_structured_accuracy
    evaluation.answer_accuracy = result.answer_accuracy
    evaluation.citation_accuracy = result.citation_accuracy
    evaluation.policy_flag_accuracy = result.policy_flag_accuracy
    evaluation.escalation_accuracy = result.escalation_accuracy
    evaluation.full_structured_match = result.full_structured_match
    evaluation.normalized_exact_match = result.normalized_exact_match
    evaluation.critical_safety_failures = result.critical_safety_failures
    evaluation.infrastructure_errors = result.infrastructure_errors
    evaluation.average_latency_seconds = result.average_latency_seconds
    evaluation.evaluation_status = "COMPLETED"
    evaluation.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(evaluation)
    return evaluation


# =========================== To fail evaluation ================================== #
def fail_evaluation(db: Session, evaluation_id: int):
    evaluation = get_evaluation_by_id(db, evaluation_id)

    if not evaluation:
        raise ValueError("Evaluation not found")

    evaluation.evaluation_status = "FAILED"
    evaluation.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(evaluation)
    return evaluation
