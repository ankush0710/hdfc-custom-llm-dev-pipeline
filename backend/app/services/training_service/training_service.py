from sqlalchemy.orm import Session

from app.model.training_model import Training_Model
from app.schema.training_schema.training_schema import TrainingRunCreate

def create_training_run(db:Session, data:TrainingRunCreate):
    training_run = Training_Model(
        dataset_version_id=data.dataset_version_id,
        base_model=data.base_model,
        training_method=data.training_method,
        epochs=data.epochs,
        learning_rate=data.learning_rate,
        batch_size=data.batch_size,
        status="CREATED",
    )

    db.add(training_run)
    db.commit()
    db.refresh(training_run)

    return training_run

