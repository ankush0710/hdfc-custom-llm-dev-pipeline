import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.ai.training_adapter.training_adapter import AITrainingAdapter
from app.constants.training_status import training_status
from app.dbConfig.database_config import SessionLocal
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.model_registry import Model_Registry
from app.model.training_job_model import TrainingJobModel
from app.model.training_model import Training_Model
from app.schema.training_schema.training_schema import TrainingRunCreate

logger = logging.getLogger(__name__)


# ================= create new training run ========================================= #
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

    # Strict governance: Enforce that only cleaned and processed datasets can be trained
    if str(dataset_version.status).strip().lower() != "processed":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dataset version {data.dataset_version_id} is not processed (current status: '{dataset_version.status}'). "
                f"Training is only allowed on cleaned and processed datasets. "
                f"Please run data preprocessing via POST /data-processing/jobs before training."
            )
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
    db.flush()

    # Automatically create the associated training job in QUEUED status
    training_job = TrainingJobModel(
        training_run_id=training_run.id,
        status=training_status.QUEUED,
        progress=0,
    )
    db.add(training_job)

    db.commit()
    db.refresh(training_run)

    return training_run



# ================= training background worker ===================================== #
def _execute_training_run_worker(run_id: int):
    """Background worker executing model training and updating DB status/registry."""
    db = SessionLocal()
    try:
        training_run = db.query(Training_Model).filter(Training_Model.id == run_id).first()
        if not training_run:
            logger.error("Training run %d not found in worker.", run_id)
            return

        training_job = (
            db.query(TrainingJobModel)
            .filter(TrainingJobModel.training_run_id == run_id)
            .order_by(TrainingJobModel.id.desc())
            .first()
        )
        if not training_job:
            training_job = TrainingJobModel(
                training_run_id=run_id,
                status=training_status.RUNNING,
                progress=10,
                started_at=datetime.utcnow()
            )
            db.add(training_job)
            db.commit()
            db.refresh(training_job)

        dataset_version = (
            db.query(Dataset_Version_Model)
            .filter(Dataset_Version_Model.id == training_run.dataset_version_id)
            .first()
        )
        if not dataset_version or not os.path.exists(dataset_version.file_path):
            raise FileNotFoundError(
                f"Dataset file '{dataset_version.file_path if dataset_version else None}' not found on disk."
            )

        output_dir = str(Path(f"ai/artifacts/runs/run_{run_id}").resolve())

        # Update progress to indicate preparation complete
        training_job.progress = 20
        db.commit()

        logger.info("Starting AI training adapter for run %d...", run_id)
        train_result = AITrainingAdapter.train(
            base_model=training_run.base_model,
            dataset_path=dataset_version.file_path,
            output_dir=output_dir,
            epochs=float(training_run.epochs),
            learning_rate=float(training_run.learning_rate),
            batch_size=int(training_run.batch_size),
        )
        logger.info("Training finished for run %d: %s", run_id, train_result)

        # Mark Run & Job as COMPLETED
        now = datetime.utcnow()
        training_job.status = training_status.COMPLETED
        training_job.progress = 100
        training_job.completed_at = now

        training_run.status = training_status.COMPLETED
        training_run.completed_at = now
        db.commit()

        # Auto-register trained model in Model_Registry
        clean_model_name = training_run.base_model.split("/")[-1].replace("-", "_").lower()
        reg_model_name = f"hdfc_{clean_model_name}_run_{run_id}"

        registered_model = Model_Registry(
            model_name=reg_model_name,
            version=f"1.{run_id}.0",
            base_model=training_run.base_model,
            artifact_path=output_dir,
            adapter_path=output_dir,
            training_job_id=training_job.id,
            status="READY",
        )
        db.add(registered_model)
        db.commit()
        logger.info("Model '%s' registered with status READY.", reg_model_name)

    except Exception as exc:
        logger.exception("Training run %d failed: %s", run_id, exc)
        now = datetime.utcnow()
        try:
            training_run = db.query(Training_Model).filter(Training_Model.id == run_id).first()
            if training_run:
                training_run.status = training_status.FAILED
                training_run.error_message = str(exc)
                training_run.completed_at = now

            training_job = (
                db.query(TrainingJobModel)
                .filter(TrainingJobModel.training_run_id == run_id)
                .order_by(TrainingJobModel.id.desc())
                .first()
            )
            if training_job:
                training_job.status = training_status.FAILED
                training_job.error_message = str(exc)
                training_job.completed_at = now

            db.commit()
        except Exception as rollback_err:
            logger.error("Failed to commit training error state: %s", rollback_err)
    finally:
        db.close()


# ================= start the training run ================================ #
def start_training_run(db: Session, run_id: int, background_tasks: Optional[BackgroundTasks] = None):
    training_run = (
        db.query(Training_Model)
        .filter(Training_Model.id == run_id)
        .first()
    )

    if not training_run:
        return None

    if training_run.status not in {training_status.CREATED, training_status.FAILED}:
        raise ValueError(f"Only CREATED or FAILED training runs can be started. Current status: '{training_run.status}'")

    dataset_version = (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == training_run.dataset_version_id)
        .first()
    )
    if not dataset_version or str(dataset_version.status).strip().lower() != "processed":
        raise ValueError(
            f"Cannot start training run: Dataset version {training_run.dataset_version_id} has status '{dataset_version.status if dataset_version else None}'. "
            f"Only cleaned and processed datasets (status: 'Processed') can be trained."
        )

    now = datetime.utcnow()
    training_run.status = training_status.RUNNING
    training_run.started_at = now
    training_run.error_message = None


    # Update or create training job
    training_job = (
        db.query(TrainingJobModel)
        .filter(TrainingJobModel.training_run_id == run_id)
        .order_by(TrainingJobModel.id.desc())
        .first()
    )
    if training_job:
        training_job.status = training_status.RUNNING
        training_job.started_at = now
        training_job.progress = 5
        training_job.error_message = None
    else:
        training_job = TrainingJobModel(
            training_run_id=run_id,
            status=training_status.RUNNING,
            started_at=now,
            progress=5
        )
        db.add(training_job)

    db.commit()
    db.refresh(training_run)

    # Launch background worker
    if background_tasks is not None:
        background_tasks.add_task(_execute_training_run_worker, run_id)
    else:
        thread = threading.Thread(target=_execute_training_run_worker, args=(run_id,), daemon=True)
        thread.start()

    return training_run


# ================= get all training runs ================================== #
def get_training_runs(db: Session):
    return (
        db.query(Training_Model)
        .order_by(Training_Model.id.desc())
        .all()
    )


# ================= get training run by id ================================= #
def get_training_run_by_id(db: Session, run_id: int):
    return (
        db.query(Training_Model)
        .filter(Training_Model.id == run_id)
        .first()
    )