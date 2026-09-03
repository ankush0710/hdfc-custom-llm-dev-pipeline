"""
backend/app/routes/inference_routes/inference_routes.py

Control plane routes for model inference.
Dispatches heavy model execution to the dedicated ML Service.
"""
from fastapi import APIRouter, Depends, HTTPException
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
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    service = InferenceService(db)
    try:
        return service.predict(
            model_id=payload.model_id,
            task_type=payload.task_type,
            question=payload.question,
            context=payload.context,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
            do_sample=payload.do_sample,
            seed=payload.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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