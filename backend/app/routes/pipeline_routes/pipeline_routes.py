"""
GET /pipeline/status/{dataset_version_id}

Returns the complete lineage snapshot for a given dataset version:
  dataset_version → processing_job → training_run → training_job
                  → model_registry → evaluation → deployment

This gives a single-call view of where the pipeline stands for any version.

GET /pipeline/dashboard/stats

Returns aggregate counts from all tables for the main dashboard.
All values come directly from PostgreSQL — no hardcoded fallbacks.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.model.dataset_processing_model import Processing_Model
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.deployment_model import Deployment
from app.model.evaluation_run_model import Evaluation_Model
from app.model.model_registry import Model_Registry
from app.model.training_job_model import TrainingJobModel
from app.model.training_model import Training_Model


router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline"],
)


# ─────────────────────── Pydantic response shapes ─────────────────────────── #

class DatasetVersionSummary(BaseModel):
    id: int
    version: str
    file_name: str
    file_type: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class ProcessingJobSummary(BaseModel):
    id: int
    status: str
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TrainingRunSummary(BaseModel):
    id: int
    base_model: str
    training_method: str
    epochs: int
    status: str
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TrainingJobSummary(BaseModel):
    id: int
    status: str
    progress: int
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ModelRegistrySummary(BaseModel):
    id: int
    model_name: str
    version: str
    base_model: str
    adapter_path: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class EvaluationSummary(BaseModel):
    evaluation_id: int
    evaluation_status: str
    total_examples: int
    normalized_exact_match: Optional[float] = None
    answer_accuracy: Optional[float] = None
    infrastructure_errors: Optional[int] = None
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class DeploymentSummary(BaseModel):
    id: int
    version: str
    environment: str
    status: str
    endpoint: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PipelineStatusResponse(BaseModel):
    dataset_version: DatasetVersionSummary
    processing_jobs: List[ProcessingJobSummary]
    training_runs: List[TrainingRunSummary]
    training_jobs: List[TrainingJobSummary]
    models: List[ModelRegistrySummary]
    evaluations: List[EvaluationSummary]
    deployments: List[DeploymentSummary]
    pipeline_stage: str          # human-readable current stage
    pipeline_complete: bool      # True when at least one DEPLOYED model exists


# ─────────────────────── Dashboard Stats shapes ────────────────────────────── #

class RecentActivityItem(BaseModel):
    id: str
    event_type: str         # "training_completed", "training_failed", "training_running",
                            # "evaluation_completed", "evaluation_failed",
                            # "model_registered", "model_deployed", "dataset_uploaded"
    title: str
    description: str
    timestamp: Optional[str] = None
    status: Optional[str] = None


class DashboardStatsResponse(BaseModel):
    total_datasets: int
    total_models: int
    active_trainings: int
    completed_trainings: int
    failed_trainings: int
    total_evaluations: int
    avg_evaluation_score: Optional[float] = None   # None when no completed evaluations
    avg_evaluation_score_str: str                  # "89.2%" or "N/A"
    active_deployments: int
    recent_activity: List[RecentActivityItem]


def _resolve_stage(
    dv_status: str,
    has_processing: bool,
    training_statuses: List[str],
    model_statuses: List[str],
    eval_statuses: List[str],
    deployment_statuses: List[str],
) -> str:
    """Return the most advanced stage the pipeline has reached."""
    if any(s == "ACTIVE" for s in deployment_statuses):
        return "DEPLOYED"
    if any(s in {"EVALUATED", "READY"} for s in model_statuses):
        return "EVALUATED"
    if any(s == "COMPLETED" for s in eval_statuses):
        return "EVALUATING"
    if any(s in {"READY", "CREATED"} for s in model_statuses):
        return "TRAINED"
    if any(s == "RUNNING" for s in training_statuses):
        return "TRAINING"
    if any(s in {"CREATED", "QUEUED"} for s in training_statuses):
        return "QUEUED_FOR_TRAINING"
    if has_processing:
        return "PROCESSED" if dv_status == "Processed" else "PROCESSING"
    return "UPLOADED"


# ─────────────────────────────── Routes ───────────────────────────────────── #

@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Aggregate dashboard statistics from real database records",
    description=(
        "Returns live counts and metrics for the main dashboard: "
        "dataset count, model count, training run counts, evaluation score average, "
        "deployment count, and recent activity feed. "
        "All values are computed from PostgreSQL — no hardcoded fallbacks."
    ),
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    from app.model.dataset_model import Dataset_Model

    # ── Counts ────────────────────────────────────────────────────────────────
    total_datasets = db.query(Dataset_Model).count()
    total_models = db.query(Model_Registry).count()
    active_deployments = (
        db.query(Deployment).filter(Deployment.status == "ACTIVE").count()
    )

    all_training_runs = db.query(Training_Model).all()
    active_trainings = sum(
        1 for r in all_training_runs
        if str(r.status or "").upper() in {"RUNNING", "QUEUED", "CREATED"}
    )
    completed_trainings = sum(
        1 for r in all_training_runs
        if str(r.status or "").upper() == "COMPLETED"
    )
    failed_trainings = sum(
        1 for r in all_training_runs
        if str(r.status or "").upper() == "FAILED"
    )

    # ── Avg evaluation score ──────────────────────────────────────────────────
    completed_evals = (
        db.query(Evaluation_Model)
        .filter(Evaluation_Model.evaluation_status == "COMPLETED")
        .all()
    )
    total_evaluations = db.query(Evaluation_Model).count()

    scores = []
    for e in completed_evals:
        raw = (
            e.answer_accuracy
            if e.answer_accuracy is not None
            else e.intent_structured_accuracy
            if e.intent_structured_accuracy is not None
            else e.full_structured_match
        )
        if raw is not None:
            pct = raw * 100 if raw <= 1.0 else raw
            scores.append(pct)

    avg_score: Optional[float] = round(sum(scores) / len(scores), 1) if scores else None
    avg_score_str = f"{avg_score}%" if avg_score is not None else "N/A"

    # ── Recent Activity Feed ──────────────────────────────────────────────────
    activity: List[RecentActivityItem] = []

    # Last 5 training runs (most recent first)
    recent_runs = (
        db.query(Training_Model)
        .order_by(Training_Model.id.desc())
        .limit(5)
        .all()
    )
    for run in recent_runs:
        run_status = str(run.status or "").upper()
        ts = run.completed_at or run.started_at or run.created_at
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None

        if run_status == "COMPLETED":
            event_type = "training_completed"
            title = f"Training Run #{run.id} Completed"
            desc = f"Base model: {run.base_model} · Method: {run.training_method}"
        elif run_status == "FAILED":
            event_type = "training_failed"
            title = f"Training Run #{run.id} Failed"
            desc = run.error_message or "Unknown error"
        elif run_status == "RUNNING":
            event_type = "training_running"
            title = f"Training Run #{run.id} In Progress"
            desc = f"Base model: {run.base_model} · {run.epochs} epochs"
        else:
            event_type = "training_queued"
            title = f"Training Run #{run.id} Queued"
            desc = f"Base model: {run.base_model}"

        activity.append(RecentActivityItem(
            id=f"run-{run.id}",
            event_type=event_type,
            title=title,
            description=desc,
            timestamp=ts_str,
            status=run.status,
        ))

    # Last 3 evaluations
    recent_evals = (
        db.query(Evaluation_Model)
        .order_by(Evaluation_Model.evaluation_id.desc())
        .limit(3)
        .all()
    )
    for ev in recent_evals:
        ev_status = str(ev.evaluation_status or "").upper()
        ts = ev.completed_at or ev.started_at or ev.created_at
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None

        if ev_status == "COMPLETED":
            event_type = "evaluation_completed"
            title = f"Evaluation #{ev.evaluation_id} Completed"
            desc = f"Run #{ev.run_id} · {ev.total_examples} examples evaluated"
        elif ev_status == "FAILED":
            event_type = "evaluation_failed"
            title = f"Evaluation #{ev.evaluation_id} Failed"
            desc = ev.error_message or "Unknown error"
        else:
            event_type = "evaluation_running"
            title = f"Evaluation #{ev.evaluation_id} {(ev.evaluation_status or '').capitalize()}"
            desc = f"Run #{ev.run_id}"

        activity.append(RecentActivityItem(
            id=f"eval-{ev.evaluation_id}",
            event_type=event_type,
            title=title,
            description=desc,
            timestamp=ts_str,
            status=ev.evaluation_status,
        ))

    # Last 2 model deployments
    recent_deployments = (
        db.query(Deployment)
        .order_by(Deployment.id.desc())
        .limit(2)
        .all()
    )
    for dep in recent_deployments:
        model_rec = (
            db.query(Model_Registry)
            .filter(Model_Registry.id == dep.model_id)
            .first()
        )
        model_name = model_rec.model_name if model_rec else f"Model-{dep.model_id}"
        ts = dep.updated_at or dep.created_at
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None

        activity.append(RecentActivityItem(
            id=f"dep-{dep.id}",
            event_type="model_deployed",
            title=f"{model_name} Deployed",
            description=f"Version {dep.version} → {dep.environment} · {dep.status}",
            timestamp=ts_str,
            status=dep.status,
        ))

    # Sort activity by timestamp descending, limit to 8 items
    def _sort_key(item: RecentActivityItem):
        return item.timestamp or ""

    activity.sort(key=_sort_key, reverse=True)
    activity = activity[:8]

    return DashboardStatsResponse(
        total_datasets=total_datasets,
        total_models=total_models,
        active_trainings=active_trainings,
        completed_trainings=completed_trainings,
        failed_trainings=failed_trainings,
        total_evaluations=total_evaluations,
        avg_evaluation_score=avg_score,
        avg_evaluation_score_str=avg_score_str,
        active_deployments=active_deployments,
        recent_activity=activity,
    )


@router.get(
    "/status/{dataset_version_id}",
    response_model=PipelineStatusResponse,
    summary="Full pipeline lineage for a dataset version",
    description=(
        "Returns a single-call snapshot of the entire pipeline state for a "
        "given dataset_version_id: processing jobs, training runs, training jobs, "
        "registered models, evaluations, and deployments."
    ),
)
def get_pipeline_status(
    dataset_version_id: int,
    db: Session = Depends(get_db),
):
    # ── 1. Dataset version ─────────────────────────────────────────────────
    dv = (
        db.query(Dataset_Version_Model)
        .filter(Dataset_Version_Model.id == dataset_version_id)
        .first()
    )
    if not dv:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset version {dataset_version_id} not found.",
        )

    # ── 2. Processing jobs ─────────────────────────────────────────────────
    processing_jobs = (
        db.query(Processing_Model)
        .filter(Processing_Model.dataset_version_id == dataset_version_id)
        .order_by(Processing_Model.id.desc())
        .all()
    )

    # ── 3. Training runs (linked via dataset_version_id) ───────────────────
    training_runs = (
        db.query(Training_Model)
        .filter(Training_Model.dataset_version_id == dataset_version_id)
        .order_by(Training_Model.id.desc())
        .all()
    )

    training_run_ids = [r.id for r in training_runs]

    # ── 4. Training jobs ───────────────────────────────────────────────────
    training_jobs: List[TrainingJobModel] = []
    if training_run_ids:
        training_jobs = (
            db.query(TrainingJobModel)
            .filter(TrainingJobModel.training_run_id.in_(training_run_ids))
            .order_by(TrainingJobModel.id.desc())
            .all()
        )

    # ── 5. Models in registry (linked via training_job_id) ─────────────────
    training_job_ids = [j.id for j in training_jobs]
    models: List[Model_Registry] = []
    if training_job_ids:
        models = (
            db.query(Model_Registry)
            .filter(Model_Registry.training_job_id.in_(training_job_ids))
            .order_by(Model_Registry.id.desc())
            .all()
        )

    model_ids = [m.id for m in models]

    # ── 6. Evaluations (linked via run_id) ────────────────────────────────
    evaluations: List[Evaluation_Model] = []
    if training_run_ids:
        evaluations = (
            db.query(Evaluation_Model)
            .filter(Evaluation_Model.run_id.in_(training_run_ids))
            .order_by(Evaluation_Model.evaluation_id.desc())
            .all()
        )

    # ── 7. Deployments (linked via model_id) ─────────────────────────────
    deployments: List[Deployment] = []
    if model_ids:
        deployments = (
            db.query(Deployment)
            .filter(Deployment.model_id.in_(model_ids))
            .order_by(Deployment.id.desc())
            .all()
        )

    # ── 8. Resolve stage label ────────────────────────────────────────────
    stage = _resolve_stage(
        dv_status=dv.status,
        has_processing=bool(processing_jobs),
        training_statuses=[r.status for r in training_runs],
        model_statuses=[m.status for m in models],
        eval_statuses=[e.evaluation_status for e in evaluations],
        deployment_statuses=[d.status for d in deployments],
    )

    return PipelineStatusResponse(
        dataset_version=dv,
        processing_jobs=processing_jobs,
        training_runs=training_runs,
        training_jobs=training_jobs,
        models=models,
        evaluations=evaluations,
        deployments=deployments,
        pipeline_stage=stage,
        pipeline_complete=any(d.status == "ACTIVE" for d in deployments),
    )
