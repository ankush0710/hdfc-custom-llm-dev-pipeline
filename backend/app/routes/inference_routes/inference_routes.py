from fastapi import APIRouter, HTTPException

from app.schema.inference_schema.inference_schema import (
    InferenceRequest,
    InferenceResponse,
)
from app.services.inference_service.inference_service import (
    InferenceService,
)


router = APIRouter(
    prefix="/inference",
    tags=["Inference"],
)


inference_service = InferenceService()


@router.post(
    "/predict",
    response_model=InferenceResponse,
)
def predict(
    payload: InferenceRequest,
):

    try:

        result = inference_service.predict(
            prompt=payload.prompt,
        )

        return result

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