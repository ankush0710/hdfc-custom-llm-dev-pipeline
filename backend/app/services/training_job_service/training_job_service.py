from sqlalchemy.orm import Session

from app.model.training_model import Training_Model
from app.model.training_job_model import TrainingJobModel
from app.constants.training_status import training_status

# ============================== To create the training jobs ============================ #
def create_training_job(
    db: Session,
    training_run_id: int
):

    training_run = (
        db.query(Training_Model)
        .filter(
            Training_Model.id == training_run_id
        )
        .first()
    )

    if not training_run:
        return None

    training_job = TrainingJobModel(
        training_run_id=training_run_id,
        status=training_status.QUEUED,
        progress=0
    )

    db.add(training_job)

    db.commit()

    db.refresh(training_job)

    return training_job

# ============================== retrieve the trainng jobs ================================= #
def get_training_jobs(
    db: Session
):

    return (
        db.query(TrainingJobModel)
        .order_by(
            TrainingJobModel.id.desc()
        )
        .all()
    )

# ============================= retrieve the training job by id ============================= #
def get_training_job_by_id(
    db: Session,
    job_id: int
):

    return (
        db.query(TrainingJobModel)
        .filter(
            TrainingJobModel.id == job_id
        )
        .first()
    )