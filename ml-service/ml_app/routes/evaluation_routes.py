"""
ml-service/app/routes/evaluation_routes.py

Routes for dispatching and stopping asynchronous model evaluation runs on the ML Service.
Protected by verify_ml_service_key.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..core.security import verify_ml_service_key
from ..services.evaluation_worker import (
    execute_evaluation_job_async,
    request_stop_evaluation,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/evaluation",
    tags=["ML Evaluation"],
    dependencies=[Depends(verify_ml_service_key)],
)


class EvaluationDispatchRequest(BaseModel):
    evaluation_id: int
    run_id: int
    model_id: int
    test_dataset_id: int


@router.post("/dispatch")
def dispatch_evaluation_job(payload: EvaluationDispatchRequest):
    """
    Accept an asynchronous model evaluation run dispatch.
    Returns 200 OK immediately without blocking HTTP requests.
    """
    try:
        execute_evaluation_job_async(
            evaluation_id=payload.evaluation_id,
            run_id=payload.run_id,
            model_id=payload.model_id,
            test_dataset_id=payload.test_dataset_id,
        )
        return {
            "status": "dispatched",
            "evaluation_id": payload.evaluation_id,
            "message": f"Evaluation #{payload.evaluation_id} successfully dispatched to ML worker.",
        }
    except Exception as exc:
        logger.exception("Failed to dispatch evaluation %d: %s", payload.evaluation_id, exc)
        raise HTTPException(status_code=500, detail=f"Failed to dispatch evaluation job: {str(exc)}")


@router.post("/stop/{evaluation_id}")
def stop_evaluation_job(evaluation_id: int):
    """Request graceful cancellation of a running evaluation run."""
    stopped = request_stop_evaluation(evaluation_id)
    return {
        "status": "stop_requested" if stopped else "not_active_in_memory",
        "evaluation_id": evaluation_id,
        "message": f"Stop signal processed for evaluation #{evaluation_id}.",
    }
