from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.model.training_model import Training_Model
from app.model.dataset_version_model import Dataset_Version_Model
from app.schema.training_schema.training_schema import TrainingRunCreate
from app.constants.training_status import training_status

# ================= create new trainnig run ========================================= # 
def create_training_run(db: Session, data: TrainingRunCreate):
    dataset_version = (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == data.dataset_version_id)
        .first()
    )
    if not dataset_version:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset version {data.dataset_version_id} not found"
        )

    training_run = Training_Model(
        dataset_version_id=data.dataset_version_id,
        base_model=data.base_model,
        training_method=data.training_method,
        epochs=data.epochs,
        learning_rate=data.learning_rate,
        batch_size=data.batch_size,
        status=training_status.CREATED,
    )

    db.add(training_run)
    db.commit()
    db.refresh(training_run)

    return training_run
    

# ================= start the training run ================================ #
def start_training_run(db: Session, run_id:int):
    training_run = (
        db.query(Training_Model)
        .filter(Training_Model.id == run_id)
        .first()
    )

    if not training_run:
        return None

    if training_run.status != training_status.CREATED:
        raise ValueError("only Created training runs can be started")

    training_run.status = training_status.RUNNING
    training_status.started_at = datetime.utcnow()

    db.commit()
    db.refresh(training_run)

    return training_run


# ================= get the all training status ============================ #
def get_training_runs(
    db: Session
):
    return (
        db.query(Training_Model)
        .order_by(Training_Model.id.desc())
        .all()
    )


# ================= get the training status by id ============================ #
def get_training_run_by_id(
    db: Session,
    run_id: int
):
    return (
        db.query(Training_Model)
        .filter(Training_Model.id == run_id)
        .first()
    )