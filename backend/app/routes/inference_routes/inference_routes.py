from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db

from app.schema.inference_schema.inference_schema import (
    InferenceRequest,
    InferenceResponse,
)

from app.services.inference_service.inference_service import (
    InferenceService,
)

from app.ai.inference_adapter.inference_adapter import (
    AIInferenceAdapter,
)


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

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/models")
def list_models():

    try:

        return (
            AIInferenceAdapter.list_models()
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/unload")
def unload_model():

    try:

        return AIInferenceAdapter.unload()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )