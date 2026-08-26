from sqlalchemy.orm import Session

from app.model.model_registry import Model_Registry
from app.model.training_job_model import TrainingJobModel
from app.model.evaluation_run_model import Evaluation_Model
from app.schema.model_registry.model_registry import Model_Create

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
    db:Session,
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
            f"Model {payload.model_name} version {payload.version} already exists",
        )

    if payload.training_job_id is not None:
        training_job = db.query(TrainingJobModel).filter(TrainingJobModel.id == payload.training_job_id).first()
        if not training_job:
            raise ValueError(f"Training job with id {payload.training_job_id} not found")

    if payload.evaluation_id is not None:
        evaluation = db.query(Evaluation_Model).filter(Evaluation_Model.evaluation_id == payload.evaluation_id).first()
        if not evaluation:
            raise ValueError(f"Evaluation with id {payload.evaluation_id} not found")

    init_status = (payload.status or "CREATED").strip().upper()
    if init_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid initial model status: '{init_status}'. Valid statuses: {sorted(VALID_STATUSES)}"
        )

    model = Model_Registry(
        model_name = payload.model_name,
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
