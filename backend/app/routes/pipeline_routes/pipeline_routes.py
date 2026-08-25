"""
GET /pipeline/status/{dataset_version_id}

Returns the complete lineage snapshot for a given dataset version:
  dataset_version → processing_job → training_run → training_job
                  → model_registry → evaluation → deployment

This gives a single-call view of where the pipeline stands for any version.
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


# ─────────────────────────────── Route ────────────────────────────────────── #

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
