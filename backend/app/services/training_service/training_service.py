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
from app.constants.supported_models import resolve_hf_model_id, resolve_model_config
from app.dbConfig.database_config import SessionLocal
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.model_registry import Model_Registry
from app.model.training_job_model import TrainingJobModel
from app.model.training_model import Training_Model
from app.schema.training_schema.training_schema import TrainingRunCreate

logger = logging.getLogger(__name__)


# ================= create new training run ========================================= #
def create_training_run(db: Session, data: TrainingRunCreate):
    # 1. Validate and resolve model to canonical HF model ID
    try:
        canonical_base_model = resolve_hf_model_id(data.base_model)
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=str(val_err)
        )

    # 2. Validate dataset version and security status
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

    # Strict governance: Enforce that only cleaned, de-identified, and processed datasets can be trained
    norm_path = (dataset_version.file_path or "").replace("\\", "/").lower()
    is_raw_path = "uploads/" in norm_path or "storage/raw" in norm_path or "/raw/" in norm_path

    if is_raw_path or str(dataset_version.status).strip().lower() != "processed" or not dataset_version.is_safe_for_training:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dataset version {data.dataset_version_id} is not safe for training (status: '{dataset_version.status}', safe_for_training: {dataset_version.is_safe_for_training}). "
                f"Training is strictly prohibited on raw datasets to protect customer PII and private banking information. "
                f"Please run data preprocessing and PII de-identification via POST /data-processing/jobs before training."
            )
        )

    training_run = Training_Model(
        dataset_version_id=data.dataset_version_id,
        base_model=canonical_base_model,
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

    setattr(training_run, "job_id", training_job.id)
    setattr(training_run, "job_status", training_job.status)
    setattr(training_run, "job_progress", training_job.progress)
    setattr(training_run, "progress", training_job.progress)

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
        raw_path = dataset_version.file_path if dataset_version else None
        if not raw_path:
            raise FileNotFoundError(f"Dataset version {training_run.dataset_version_id} has no file path configured.")

        ds_path = raw_path if os.path.exists(raw_path) else str(Path(raw_path).resolve())
        if not os.path.exists(ds_path):
            raise FileNotFoundError(f"Dataset file '{raw_path}' not found on disk.")

        output_dir = str(Path(f"ai/artifacts/runs/run_{run_id}").resolve())

        # Update progress to indicate preparation complete
        training_job.progress = 20
        db.commit()

        canonical_base_model = resolve_hf_model_id(training_run.base_model)
        logger.info("Starting AI training adapter for run %d with base model '%s'...", run_id, canonical_base_model)

        def _on_step_progress(pct: int, step: int, max_steps: int):
            logger.info(
                "DATABASE CALLBACK RECEIVED: percentage=%d, step=%d, max_steps=%d",
                pct,
                step,
                max_steps,
            )
            progress_db = None

            try:
                progress_db = SessionLocal()

                job = (
                    progress_db.query(TrainingJobModel)
                    .filter(TrainingJobModel.training_run_id == run_id)
                    .order_by(TrainingJobModel.id.desc())
                    .first()
                )

                if not job:
                    logger.error(
                        "Progress update failed: no TrainingJob found for run %d",
                        run_id,
                    )
                    return

                # Keep progress between 0 and 99 while training is running
                safe_progress = max(0, min(99, int(pct)))

                # Ensure progress never moves backwards
                if job.progress is not None and safe_progress < job.progress:
                    safe_progress = job.progress

                # Save the actual trainer progress immediately
                job.progress = safe_progress
                job.status = training_status.RUNNING

                progress_db.commit()
                progress_db.refresh(job)

                logger.info(
                    "DATABASE PROGRESS SAVED: run_id=%d, job_id=%d, progress=%d",
                    run_id,
                    job.id,
                    safe_progress,
                )

            except Exception:
                logger.exception(
                    "Progress callback FAILED for training run %d",
                    run_id,
                )

                if progress_db:
                    progress_db.rollback()

            finally:
                if progress_db:
                    progress_db.close()

        train_result = AITrainingAdapter.train(
            base_model=canonical_base_model,
            dataset_path=ds_path,
            output_dir=output_dir,
            epochs=float(training_run.epochs),
            learning_rate=float(training_run.learning_rate),
            batch_size=int(training_run.batch_size),
            progress_callback=_on_step_progress,
        )
        logger.info("Training finished for run %d: %s", run_id, train_result)

        # Mark Run & Job as COMPLETED
        now = datetime.utcnow()

        # Expire all cached objects in worker session to avoid stale state
        db.expire_all()

        training_job = (
            db.query(TrainingJobModel)
            .filter(TrainingJobModel.training_run_id == run_id)
            .order_by(TrainingJobModel.id.desc())
            .first()
        )
        training_run = (
            db.query(Training_Model)
            .filter(Training_Model.id == run_id)
            .first()
        )

        if training_job:
            training_job.status = training_status.COMPLETED
            training_job.progress = 100
            training_job.completed_at = now

        if training_run:
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

    current_run_status = str(training_run.status or "").upper()
    if current_run_status not in {training_status.CREATED, training_status.QUEUED, training_status.FAILED, "CREATED", "QUEUED", "FAILED", "READY"}:
        raise ValueError(f"Only CREATED, QUEUED, or FAILED training runs can be started. Current status: '{training_run.status}'")

    dataset_version = (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == training_run.dataset_version_id)
        .first()
    )
    if not dataset_version:
        raise ValueError(f"Dataset version {training_run.dataset_version_id} not found in database.")

    norm_path = (dataset_version.file_path or "").replace("\\", "/").lower()
    is_raw_path = "uploads/" in norm_path or "storage/raw" in norm_path or "/raw/" in norm_path

    if is_raw_path or str(dataset_version.status).strip().lower() != "processed" or not dataset_version.is_safe_for_training:
        raise ValueError(
            f"Cannot start training run: Dataset version {training_run.dataset_version_id} is not safe for training. "
            f"Only processed, PII-sanitized datasets can be trained."
        )

    file_exists = False
    if dataset_version.file_path:
        file_exists = os.path.exists(dataset_version.file_path) or Path(dataset_version.file_path).resolve().exists()

    if not file_exists:
        raise ValueError(
            f"Cannot start training run: Dataset version {training_run.dataset_version_id} file not found on disk at '{dataset_version.file_path}'."
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

    setattr(training_run, "job_id", training_job.id)
    setattr(training_run, "job_status", training_job.status)
    setattr(training_run, "job_progress", training_job.progress)
    setattr(training_run, "progress", training_job.progress)

    return training_run


# ================= get all training runs ================================== #
def get_training_runs(db: Session):
    runs = (
        db.query(Training_Model)
        .order_by(Training_Model.id.desc())
        .all()
    )
    if not runs:
        return []

    # Batch query latest training jobs for all runs to avoid N+1 queries
    run_ids = [r.id for r in runs]
    jobs = (
        db.query(TrainingJobModel)
        .filter(TrainingJobModel.training_run_id.in_(run_ids))
        .order_by(TrainingJobModel.id.desc())
        .all()
    )

    latest_jobs = {}
    for j in jobs:
        if j.training_run_id not in latest_jobs:
            latest_jobs[j.training_run_id] = j

    results = []
    for r in runs:
        job = latest_jobs.get(r.id)
        prog = job.progress if (job and job.progress is not None) else (100 if str(r.status).upper() == "COMPLETED" else 0)
        setattr(r, "job_id", job.id if job else None)
        setattr(r, "job_status", job.status if job else None)
        setattr(r, "job_progress", prog)
        setattr(r, "progress", prog)
        logger.info(
            "GET /training/runs → Run #%d: status=%s, progress=%s, job_progress=%s",
            r.id,
            r.status,
            prog,
            prog,
        )
        results.append(r)
    return results


# ================= get training run by id ================================= #
def get_training_run_by_id(db: Session, run_id: int):
    r = (
        db.query(Training_Model)
        .filter(Training_Model.id == run_id)
        .first()
    )
    if not r:
        return None

    job = (
        db.query(TrainingJobModel)
        .filter(TrainingJobModel.training_run_id == run_id)
        .order_by(TrainingJobModel.id.desc())
        .first()
    )
    prog = job.progress if job else (100 if str(r.status).upper() == "COMPLETED" else 0)
    setattr(r, "job_id", job.id if job else None)
    setattr(r, "job_status", job.status if job else None)
    setattr(r, "job_progress", prog)
    setattr(r, "progress", prog)
    return r
