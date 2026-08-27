from sqlalchemy.orm import Session
from pathlib import Path

from app.model.model_registry import Model_Registry
from app.model.training_job_model import TrainingJobModel
from app.model.evaluation_run_model import Evaluation_Model
from app.schema.model_registry.model_registry import Model_Create
from app.core.path_utils import resolve_artifact_path, validate_artifact_directory

VALID_STATUSES = {
    "CREATED",
    "TRAINING",
    "TRAINED",
    "EVALUATING",
    "EVALUATED",
    "APPROVED",
    "REJECTED",
    "READY",
    "ACTIVE",
    "DEPLOYED",
    "DEPRECATED",
    "ARCHIVED",
}


def create_model(
    db: Session,
    payload: Model_Create, 
) -> Model_Registry:

    existing = (
        db.query(Model_Registry).filter(
            Model_Registry.model_name == payload.model_name,
            Model_Registry.version == payload.version,
        ).first()
    )
    
    if existing:
        raise ValueError(
            f"Model '{payload.model_name}' version '{payload.version}' already exists in Model Registry.",
        )

    # 1. Validate training job linkage if provided
    if payload.training_job_id is not None:
        training_job = db.query(TrainingJobModel).filter(TrainingJobModel.id == payload.training_job_id).first()
        if not training_job:
            raise ValueError(f"Training job with id {payload.training_job_id} not found in database.")
        
        # Auto-resolve artifact path from training job if not explicitly provided
        if not payload.artifact_path and not payload.adapter_path:
            run_path_str = f"backend/ai/artifacts/runs/run_{training_job.training_run_id}"
            resolved_run = resolve_artifact_path(run_path_str)
            if resolved_run:
                payload.artifact_path = str(resolved_run)
                payload.adapter_path = str(resolved_run)

    # 2. Validate evaluation record linkage if provided
    if payload.evaluation_id is not None:
        evaluation = db.query(Evaluation_Model).filter(Evaluation_Model.evaluation_id == payload.evaluation_id).first()
        if not evaluation:
            raise ValueError(f"Evaluation with id {payload.evaluation_id} not found in database.")

    # 3. Validate artifact/adapter path on disk
    target_path = payload.adapter_path or payload.artifact_path
    if target_path:
        validation = validate_artifact_directory(target_path)
        if not validation["is_valid"]:
            raise ValueError(
                f"Model registration failed: {validation['error_message']}"
            )
        # Store canonical resolved path
        resolved_str = str(validation["resolved_path"])
        payload.artifact_path = resolved_str
        payload.adapter_path = resolved_str
        # If adapter config specified base model and base model wasn't set, use it
        if validation.get("base_model") and not payload.base_model:
            payload.base_model = validation["base_model"]

    init_status = (payload.status or "CREATED").strip().upper()
    if init_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid initial model status: '{init_status}'. Valid statuses: {sorted(VALID_STATUSES)}"
        )

    model = Model_Registry(
        model_name=payload.model_name,
        version=payload.version,
        base_model=payload.base_model,
        artifact_path=payload.artifact_path,
        adapter_path=payload.adapter_path,
        training_job_id=payload.training_job_id,
        evaluation_id=payload.evaluation_id,
        status=init_status,
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return model


def get_model(
    db: Session,
    model_id: int
):
    return(
        db.query(Model_Registry).filter(Model_Registry.id == model_id).first()

    )

def list_model(db: Session):
    return(
        db.query(Model_Registry)
        .order_by(Model_Registry.created_at.desc())
        .all()  
    )


def update_status(
    db: Session,
    model_id: int,
    new_status: str,
):
    new_status = new_status.strip().upper()

    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid model status: '{new_status}'. Valid statuses: {sorted(VALID_STATUSES)}"
        )

    model = get_model(db, model_id)

    if not model:
        raise ValueError(f"Model with id {model_id} not found")

    model.status = new_status

    db.commit()
    db.refresh(model)

    return model
