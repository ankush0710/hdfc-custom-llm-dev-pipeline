from sqlalchemy.orm import Session

from app.model.training_model import Training_Model
from app.schema.training_schema.training_schema import TrainingRunCreate
from app.constants.training_status import training_status

def create_training_run(db:Session, data:TrainingRunCreate):
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

# =============== get the all training status ========================= #
def get_training_runs(
    db: Session
):
    return (
        db.query(TrainingRun)
        .order_by(TrainingRun.id.desc())
        .all()
    )


# =============== get the training status by id ========================= #
def get_training_run_by_id(
    db: Session,
    run_id: int
):
    return (
        db.query(TrainingRun)
        .filter(TrainingRun.id == run_id)
        .first()
    )