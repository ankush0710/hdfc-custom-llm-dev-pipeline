"""
backend/app/routes/inference_routes/inference_routes.py

Control plane routes for model inference.
Dispatches heavy model execution to the dedicated ML Service.
"""
import logging
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.clients.ml_client import MLClient
from app.core.auth_dependency import get_current_user, require_roles
from app.dbConfig.database_config import get_db
from app.model.user_model import User_Model
from app.schema.inference_schema.inference_schema import (
    InferenceRequest,
    InferenceResponse,
)
from app.services.inference_service.inference_service import InferenceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inference",
    tags=["Inference"],
)


@router.post(
    "/predict",
    response_model=InferenceResponse,
)
def predict(
    payload: InferenceRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:10]}"
    start_time = time.perf_counter()
    logger.info(
        "INFERENCE_REQUEST_RECEIVED request_id=%s model_id=%s task_type=%s",
        request_id, payload.model_id, payload.task_type
    )
    service = InferenceService(db)
    try:
        result = service.predict(
            model_id=payload.model_id,
            task_type=payload.task_type,
            question=payload.question,
            context=payload.context,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
            do_sample=payload.do_sample,
            seed=payload.seed,
            request_id=request_id,
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "INFERENCE_RESPONSE request_id=%s status_code=200 duration_ms=%.2f",
            request_id, duration_ms
        )
        return result
    except ValueError as exc:
        logger.warning(
            "INFERENCE_ERROR request_id=%s status_code=400 error_type=ValidationError upstream=backend detail=%s",
            request_id, exc
        )
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException as exc:
        logger.warning(
            "INFERENCE_ERROR request_id=%s status_code=%d error_type=HTTPException upstream=ml_service detail=%s",
            request_id, exc.status_code, exc.detail
        )
        raise
    except Exception as exc:
        logger.exception(
            "INFERENCE_ERROR request_id=%s status_code=500 error_type=UnhandledException upstream=backend detail=%s",
            request_id, exc
        )
        raise HTTPException(status_code=500, detail="Unable to generate a response due to a server error.")


@router.get("/models")
def list_models(
    current_user: User_Model = Depends(get_current_user),
):
    try:
        return MLClient.list_models()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/unload")
def unload_model(
    current_user: User_Model = Depends(require_roles("ADMIN", "DS")),
):
    try:
        return MLClient.unload_model()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))