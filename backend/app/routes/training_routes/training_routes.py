from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user, require_roles
from app.dbConfig.database_config import get_db
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.training_job_model import TrainingJobModel
from app.model.user_model import User_Model
from app.schema.training_schema.training_schema import (TrainingRunCreate, TrainingRunResponse)
from app.services.training_service.training_service import (
    create_training_run,
    get_training_runs,
    get_training_run_by_id,
    start_training_run,
)

router = APIRouter(
    prefix="/training",
    tags=["Training"]
)


# ─── Extra response schemas for detail + logs ─────────────────────────────── #

class TrainingRunDetailResponse(BaseModel):
    id: int
    dataset_version_id: int
    dataset_name: Optional[str] = None
    dataset_version_label: Optional[str] = None
    base_model: str
    training_method: str
    epochs: int
    learning_rate: float
    batch_size: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Training job fields (if exists)
    job_id: Optional[int] = None
    job_status: Optional[str] = None
    job_progress: Optional[int] = None
    # Model Registry fields (if registered)
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    huggingface_repo: Optional[str] = None
    huggingface_path: Optional[str] = None
    commit_hash: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)



class TrainingLogEntry(BaseModel):
    timestamp: Optional[str] = None
    level: str            # "INFO", "ERROR", "WARNING"
    message: str


class TrainingRunLogsResponse(BaseModel):
    run_id: int
    status: str
    error_message: Optional[str] = None
    job_id: Optional[int] = None
    job_status: Optional[str] = None
    job_progress: Optional[int] = None
    logs: List[TrainingLogEntry]


# ─────────────────────────────── Routes ───────────────────────────────────── #

@router.post(
    "/runs",
    response_model=TrainingRunResponse
)
def create_run(
    training_data: TrainingRunCreate,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_roles("ADMIN", "DS")),
):
    try:
        return create_training_run(db, training_data)
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create training run: {str(error)}"
        )


@router.post(
    "/runs/{run_id}/start",
    response_model=TrainingRunResponse
)
def start_run(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_roles("ADMIN", "DS")),
):
    try:
        training_run = start_training_run(
            db=db,
            run_id=run_id,
            background_tasks=background_tasks,
        )

        if not training_run:
            raise HTTPException(
                status_code=404,
                detail="training not found"
            )

        return training_run

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get(
    "/runs",
    response_model=list[TrainingRunResponse]
)
def get_all_runs(
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    return get_training_runs(db)


@router.get(
    "/runs/{run_id}",
    response_model=TrainingRunResponse
)
def get_run_by_id(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    training_run = get_training_run_by_id(db, run_id)

    if not training_run:
        raise HTTPException(
            status_code=404,
            detail="Training run not found"
        )

    return training_run


@router.get(
    "/runs/{run_id}/detail",
    response_model=TrainingRunDetailResponse,
    summary="Get enriched training run details including dataset and job info",
)
def get_run_detail(
    run_id: int,
    db: Session = Depends(get_db)
):
    from app.model.dataset_model import Dataset_Model

    training_run = get_training_run_by_id(db, run_id)
    if not training_run:
        raise HTTPException(status_code=404, detail="Training run not found")

    # Resolve dataset info
    dataset_name: Optional[str] = None
    dataset_version_label: Optional[str] = None
    d_ver = (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == training_run.dataset_version_id)
        .first()
    )
    if d_ver:
        dataset_version_label = f"v{d_ver.version}"
        if d_ver.dataset:
            dataset_name = d_ver.dataset.dataset_name

    job = (
        db.query(TrainingJobModel)
        .filter(TrainingJobModel.training_run_id == run_id)
        .order_by(TrainingJobModel.id.desc())
        .first()
    )

    from app.model.model_registry import Model_Registry
    model_record = None
    if job:
        model_record = (
            db.query(Model_Registry)
            .filter(Model_Registry.training_job_id == job.id)
            .first()
        )
    if not model_record:
        model_record = (
            db.query(Model_Registry)
            .filter(Model_Registry.model_name.like(f"%run_{run_id}%"))
            .first()
        )

    return TrainingRunDetailResponse(
        id=training_run.id,
        dataset_version_id=training_run.dataset_version_id,
        dataset_name=dataset_name,
        dataset_version_label=dataset_version_label,
        base_model=training_run.base_model,
        training_method=training_run.training_method,
        epochs=training_run.epochs,
        learning_rate=training_run.learning_rate,
        batch_size=training_run.batch_size,
        status=training_run.status,
        error_message=training_run.error_message,
        created_at=training_run.created_at,
        started_at=training_run.started_at,
        completed_at=training_run.completed_at,
        job_id=job.id if job else None,
        job_status=job.status if job else None,
        job_progress=job.progress if job else None,
        model_id=model_record.id if model_record else None,
        model_name=model_record.model_name if model_record else None,
        huggingface_repo=model_record.huggingface_repo if model_record else None,
        huggingface_path=model_record.huggingface_path if model_record else None,
        commit_hash=model_record.commit_hash if model_record else None,
    )



@router.get(
    "/runs/{run_id}/logs",
    response_model=TrainingRunLogsResponse,
    summary="Get training run logs and job progress",
)
def get_run_logs(
    run_id: int,
    db: Session = Depends(get_db)
):
    training_run = get_training_run_by_id(db, run_id)
    if not training_run:
        raise HTTPException(status_code=404, detail="Training run not found")

    job = (
        db.query(TrainingJobModel)
        .filter(TrainingJobModel.training_run_id == run_id)
        .order_by(TrainingJobModel.id.desc())
        .first()
    )

    logs: List[TrainingLogEntry] = []

    # Build log entries from real DB timestamps and state
    if training_run.created_at:
        logs.append(TrainingLogEntry(
            timestamp=training_run.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="INFO",
            message=f"Training run #{run_id} created. Model: {training_run.base_model}, Method: {training_run.training_method}",
        ))

    if training_run.started_at:
        logs.append(TrainingLogEntry(
            timestamp=training_run.started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="INFO",
            message=f"Training started. Epochs: {training_run.epochs}, LR: {training_run.learning_rate}, Batch: {training_run.batch_size}",
        ))

    if job and job.started_at:
        logs.append(TrainingLogEntry(
            timestamp=job.started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="INFO",
            message=f"Training job #{job.id} started. Worker dispatched.",
        ))

    run_status = str(training_run.status or "").upper()
    if run_status == "COMPLETED" and training_run.completed_at:
        logs.append(TrainingLogEntry(
            timestamp=training_run.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="INFO",
            message="Training completed successfully. Model artifacts saved and registered.",
        ))
    elif run_status == "FAILED" and training_run.completed_at:
        logs.append(TrainingLogEntry(
            timestamp=training_run.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="ERROR",
            message=f"Training FAILED: {training_run.error_message or 'Unknown error'}",
        ))
    elif run_status == "RUNNING":
        progress_pct = job.progress if job else 0
        logs.append(TrainingLogEntry(
            timestamp=None,
            level="INFO",
            message=f"Training in progress. Job progress: {progress_pct}%",
        ))

    # Sort logs by timestamp
    logs.sort(key=lambda x: x.timestamp or "")

    return TrainingRunLogsResponse(
        run_id=run_id,
        status=training_run.status,
        error_message=training_run.error_message,
        job_id=job.id if job else None,
        job_status=job.status if job else None,
        job_progress=job.progress if job else None,
        logs=logs,
    )
