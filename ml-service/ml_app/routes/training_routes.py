"""
ml-service/app/routes/training_routes.py

Routes for dispatching and stopping asynchronous training jobs on the ML Service.
Protected by verify_ml_service_key.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.security import verify_ml_service_key
from ..services.training_worker import execute_training_job_async, request_stop_training

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/training",
    tags=["ML Training"],
    dependencies=[Depends(verify_ml_service_key)],
)


class TrainingDispatchRequest(BaseModel):
    run_id: int
    base_model: str
    dataset_version_id: int
    epochs: float = Field(default=1.0, ge=0.1)
    learning_rate: float = Field(default=2e-4)
    batch_size: int = Field(default=1, ge=1)
    training_method: str = "lora"


@router.post("/dispatch")
def dispatch_training_job(payload: TrainingDispatchRequest):
    """
    Accept an asynchronous training run dispatch.
    Immediately returns 200 OK so the caller HTTP connection is NOT blocked.
    The ML service handles execution, progress callbacks, and DB updates in the background.
    """
    try:
        execute_training_job_async(
            run_id=payload.run_id,
            base_model=payload.base_model,
            dataset_version_id=payload.dataset_version_id,
            epochs=payload.epochs,
            learning_rate=payload.learning_rate,
            batch_size=payload.batch_size,
            training_method=payload.training_method,
        )
        return {
            "status": "dispatched",
            "run_id": payload.run_id,
            "message": f"Training run #{payload.run_id} successfully dispatched to background ML worker.",
        }
    except Exception as exc:
        logger.exception("Failed to dispatch training run %d: %s", payload.run_id, exc)
        raise HTTPException(status_code=500, detail=f"Failed to dispatch training job: {str(exc)}")


@router.post("/stop/{run_id}")
def stop_training_job(run_id: int):
    """Request graceful cancellation of a running training run."""
    stopped = request_stop_training(run_id)
    return {
        "status": "stop_requested" if stopped else "not_active_in_memory",
        "run_id": run_id,
        "message": f"Stop signal processed for run #{run_id}.",
    }
