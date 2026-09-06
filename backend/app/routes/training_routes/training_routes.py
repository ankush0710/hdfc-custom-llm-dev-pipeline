import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user, require_permission, require_roles
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
    stop_training_run,
)


def _to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is offset-naive in UTC for safe arithmetic with datetime.utcnow()."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


router = APIRouter(
    prefix="/training",
    tags=["Training"]
)



# ─── Extra response schemas for detail + logs ─────────────────────────────── #

class TrainingMetricPoint(BaseModel):
    step: int
    loss: Optional[float] = None
    lr: Optional[float] = None
    accuracy: Optional[float] = None


class TrainingRunDetailResponse(BaseModel):
    id: int
    dataset_version_id: int
    dataset_name: Optional[str] = None
    dataset_version_label: Optional[str] = None
    dataset_row_count: Optional[int] = None
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
    # Real trainer metrics from DB (null when not yet available)
    training_loss: Optional[float] = None
    current_lr: Optional[float] = None
    token_accuracy: Optional[float] = None
    metric_history: List[TrainingMetricPoint] = []
    # Dynamic runtime tracking fields
    creator_name: Optional[str] = "HDFC Data Scientist"
    started_time_ago: Optional[str] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    time_remaining_formatted: Optional[str] = None
    elapsed_formatted: Optional[str] = None
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
    current_user: User_Model = Depends(require_permission("training:create")),
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
    current_user: User_Model = Depends(require_permission("training:start")),
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


@router.post(
    "/runs/{run_id}/stop",
    response_model=TrainingRunResponse
)
def stop_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("training:cancel")),
):
    try:
        return stop_training_run(db=db, run_id=run_id)
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
            detail=f"Failed to stop training run: {str(error)}"
        )


@router.get(

    "/runs",
    response_model=list[TrainingRunResponse]
)
def get_all_runs(
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("training:read")),
):
    return get_training_runs(db)


@router.get(
    "/runs/{run_id}",
    response_model=TrainingRunResponse
)
def get_run_by_id(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("training:read")),
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
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("training:read")),
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

    # Resolve progress
    prog = 0
    if job and job.progress is not None:
        prog = job.progress
    elif str(training_run.status).upper() == "COMPLETED":
        prog = 100

    total_epochs = training_run.epochs or 1
    # Use real step counts from DB if available; otherwise check log_entries, otherwise estimate
    if job and job.max_steps:
        total_steps = job.max_steps
        if str(training_run.status).upper() == "COMPLETED":
            current_step = total_steps
        elif job.current_step is not None:
            current_step = job.current_step
        else:
            current_step = int((prog / 100.0) * total_steps)
    elif job and job.log_entries:
        try:
            entries = json.loads(job.log_entries)
            if entries and isinstance(entries, list):
                last_step = entries[-1].get("step")
                if last_step:
                    total_steps = max(last_step, int(last_step / (prog / 100.0))) if prog > 0 else last_step
                    current_step = total_steps if str(training_run.status).upper() == "COMPLETED" else last_step
                else:
                    total_steps = max(500, int(total_epochs * 1500))
                    current_step = total_steps if str(training_run.status).upper() == "COMPLETED" else int((prog / 100.0) * total_steps)
            else:
                total_steps = max(500, int(total_epochs * 1500))
                current_step = total_steps if str(training_run.status).upper() == "COMPLETED" else int((prog / 100.0) * total_steps)
        except Exception:
            total_steps = max(500, int(total_epochs * 1500))
            current_step = total_steps if str(training_run.status).upper() == "COMPLETED" else int((prog / 100.0) * total_steps)
    else:
        total_steps = max(500, int(total_epochs * 1500))
        current_step = total_steps if str(training_run.status).upper() == "COMPLETED" else int((prog / 100.0) * total_steps)
    if prog >= 100:
        current_epoch = total_epochs
    elif prog > 0:
        current_epoch = min(total_epochs, max(1, int(1 + (prog / 100.0) * total_epochs - 0.001)))
    else:
        current_epoch = 1

    now = datetime.utcnow()
    started_at_naive = _to_naive_utc(training_run.started_at)
    completed_at_naive = _to_naive_utc(training_run.completed_at)

    started_time_ago = "Not started yet"
    elapsed_formatted = "0s"
    time_remaining_formatted = "Ready to start"

    if started_at_naive:
        secs_ago = max(0, int((now - started_at_naive).total_seconds()))
        if secs_ago < 60:
            started_time_ago = f"Started {secs_ago}s ago"
        elif secs_ago < 3600:
            started_time_ago = f"Started {secs_ago // 60}m ago"
        elif secs_ago < 86400:
            started_time_ago = f"Started {secs_ago // 3600} hours ago"
        else:
            started_time_ago = f"Started {secs_ago // 86400} days ago"

        end_ref = completed_at_naive or now
        elapsed_secs = max(0, int((end_ref - started_at_naive).total_seconds()))
        e_hrs, e_rem = divmod(elapsed_secs, 3600)
        e_mins, e_secs = divmod(e_rem, 60)
        if e_hrs > 0:
            elapsed_formatted = f"{e_hrs}h {e_mins}m"
        elif e_mins > 0:
            elapsed_formatted = f"{e_mins}m {e_secs}s"
        else:
            elapsed_formatted = f"{e_secs}s"

        run_status = str(training_run.status or "").upper()
        if run_status == "RUNNING" and prog > 0:
            total_est = int(elapsed_secs / (prog / 100.0))
            rem_secs = max(0, total_est - elapsed_secs)
            r_hrs, r_rem = divmod(rem_secs, 3600)
            r_mins = r_rem // 60
            if r_hrs > 0:
                time_remaining_formatted = f"{r_hrs}h {r_mins}m remaining"
            else:
                time_remaining_formatted = f"{max(1, r_mins)}m remaining"
        elif run_status == "COMPLETED":
            time_remaining_formatted = "Completed"
        elif run_status == "FAILED":
            time_remaining_formatted = "Failed"
        elif run_status == "STOPPED":
            time_remaining_formatted = "Stopped"


    # Resolve real metrics from DB (no fabrication)
    real_train_loss: Optional[float] = None
    real_current_lr: Optional[float] = None
    metric_history: List[TrainingMetricPoint] = []

    if job:
        if job.train_loss is not None:
            real_train_loss = round(float(job.train_loss), 6)
        if job.current_lr is not None:
            real_current_lr = round(float(job.current_lr), 8)

        # Parse log_entries for sparkline chart data
        if job.log_entries:
            try:
                raw_entries = json.loads(job.log_entries)
                if isinstance(raw_entries, list):
                    # Sample to at most 20 evenly-spaced points for chart
                    total = len(raw_entries)
                    if total <= 20:
                        sampled = raw_entries
                    else:
                        step_size = total / 20
                        sampled = [raw_entries[int(i * step_size)] for i in range(20)]
                        # Always include the last entry
                        if raw_entries[-1] not in sampled:
                            sampled.append(raw_entries[-1])

                    for e in sampled:
                        metric_history.append(TrainingMetricPoint(
                            step=int(e.get("step", 0)),
                            loss=round(float(e["loss"]), 6) if e.get("loss") is not None else None,
                            lr=round(float(e["lr"]), 8) if e.get("lr") is not None else None,
                            accuracy=None,  # SFTTrainer does not produce token accuracy
                        ))
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    return TrainingRunDetailResponse(
        id=training_run.id,
        dataset_version_id=training_run.dataset_version_id,
        dataset_name=dataset_name,
        dataset_version_label=dataset_version_label,
        dataset_row_count=getattr(d_ver, "row_count", None) if d_ver else None,
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
        job_progress=prog,
        model_id=model_record.id if model_record else None,
        model_name=model_record.model_name if model_record else None,
        huggingface_repo=model_record.huggingface_repo if model_record else None,
        huggingface_path=model_record.huggingface_path if model_record else None,
        commit_hash=model_record.commit_hash if model_record else None,
        creator_name="HDFC Data Scientist",
        started_time_ago=started_time_ago,
        current_step=current_step,
        total_steps=total_steps,
        current_epoch=current_epoch,
        total_epochs=total_epochs,
        time_remaining_formatted=time_remaining_formatted,
        elapsed_formatted=elapsed_formatted,
        training_loss=real_train_loss,
        current_lr=real_current_lr,
        token_accuracy=None,  # Not produced by SFTTrainer
        metric_history=metric_history,
    )



@router.get(
    "/runs/{run_id}/logs",
    response_model=TrainingRunLogsResponse,
    summary="Get training run logs and job progress",
)
def get_run_logs(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("training:read")),
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

    d_ver = (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == training_run.dataset_version_id)
        .first()
    )
    dataset_name = d_ver.dataset.dataset_name if (d_ver and d_ver.dataset) else f"HDFC Dataset v{training_run.dataset_version_id}"
    version_label = f"v{d_ver.version}" if d_ver else "v1.0"

    prog = job.progress if (job and job.progress is not None) else (100 if str(training_run.status).upper() == "COMPLETED" else 0)
    total_epochs = training_run.epochs or 1
    total_steps = max(500, int(total_epochs * 1500))
    current_step = int((prog / 100.0) * total_steps)
    current_epoch = min(total_epochs, max(1, int(1 + (prog / 100.0) * total_epochs - (0.001 if prog < 100 else 0)))) if prog > 0 else 1

    start_time = _to_naive_utc(training_run.started_at) or _to_naive_utc(training_run.created_at) or datetime.utcnow()

    # Serve real log entries from DB; fall back to minimal honest header lines
    logs: List[TrainingLogEntry] = []

    # Always include a job-started marker from the actual started_at
    t0 = start_time.strftime("%H:%M:%S")
    logs.append(TrainingLogEntry(
        timestamp=t0,
        level="INFO",
        message=f"[{t0}] Training run #{run_id} started. Base model: {training_run.base_model} | Method: {training_run.training_method}",
    ))

    # Serve real step entries from DB log_entries JSON
    if job and job.log_entries:
        try:
            raw_entries = json.loads(job.log_entries)
            if isinstance(raw_entries, list):
                for e in raw_entries:
                    entry_ts = e.get("ts", "")
                    if entry_ts:
                        try:
                            entry_ts = datetime.fromisoformat(entry_ts).strftime("%H:%M:%S")
                        except (ValueError, TypeError):
                            pass
                    step_num = e.get("step", 0)
                    step_pct = e.get("pct", 0)
                    loss_val = e.get("loss")
                    lr_val = e.get("lr")

                    parts = [f"Step {step_num} | {step_pct}%"]
                    if loss_val is not None:
                        parts.append(f"Loss: {loss_val:.4f}")
                    if lr_val is not None:
                        parts.append(f"LR: {lr_val:.2e}")

                    logs.append(TrainingLogEntry(
                        timestamp=entry_ts,
                        level="INFO",
                        message=f"[{entry_ts}] {' | '.join(parts)}",
                    ))
        except (json.JSONDecodeError, TypeError):
            pass

    run_status = str(training_run.status or "").upper()
    if run_status == "COMPLETED":
        end_time = _to_naive_utc(training_run.completed_at) or (start_time + timedelta(minutes=15))
        t_end = end_time.strftime("%H:%M:%S")
        logs.append(TrainingLogEntry(
            timestamp=t_end,
            level="INFO",
            message=f"[{t_end}] Training completed successfully.",
        ))
    elif run_status == "FAILED":
        end_time = _to_naive_utc(training_run.completed_at) or (start_time + timedelta(minutes=5))
        t_end = end_time.strftime("%H:%M:%S")
        logs.append(TrainingLogEntry(
            timestamp=t_end,
            level="ERROR",
            message=f"[{t_end}] Training FAILED: {training_run.error_message or 'Execution encountered fatal error.'}",
        ))
    elif run_status in {"STOPPED", "CANCELLED"}:
        end_time = _to_naive_utc(training_run.completed_at) or (start_time + timedelta(minutes=5))
        t_end = end_time.strftime("%H:%M:%S")
        logs.append(TrainingLogEntry(
            timestamp=t_end,
            level="WARNING",
            message=f"[{t_end}] Training run stopped by user request.",
        ))

    return TrainingRunLogsResponse(
        run_id=run_id,
        status=training_run.status,
        error_message=training_run.error_message,
        job_id=job.id if job else None,
        job_status=job.status if job else None,
        job_progress=prog,
        logs=logs,
    )

