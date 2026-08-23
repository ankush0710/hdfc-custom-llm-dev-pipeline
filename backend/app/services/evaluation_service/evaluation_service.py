from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.model.evaluation_run_model import Evaluation_Model
from app.schema.evaluation_schema.evaluation_schema import EvaluationCreate, EvaluationResult


# ================================ create the evaluation runs ====================================== #
def create_evaluation(db: Session, payload: EvaluationCreate):
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


# =========================== To start the evaluation run ================================== #
def start_evaluation(db: Session, evaluation_id: int):
    evaluation = get_evaluation_by_id(db, evaluation_id)

    if not evaluation:
        raise ValueError("Evaluation not found")

    if evaluation.evaluation_status == "COMPLETED":
        raise ValueError("Evaluation is already completed")

    try:
        evaluation.evaluation_status = "RUNNING"
        evaluation.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    except Exception as exc:
        db.rollback()
        fail_eval = get_evaluation_by_id(db, evaluation_id)
        if fail_eval:
            fail_eval.evaluation_status = "FAILED"
            fail_eval.error_message = str(exc)
            fail_eval.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise


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



