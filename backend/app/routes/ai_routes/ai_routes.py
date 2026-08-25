from fastapi import APIRouter, HTTPException

from app.schema.ai_schema.ai_schema import (
    AIInferenceRequest,
    AIInferenceResponse,
)

from app.services.ai_service.ai_service import AIService

from ai.inference.service import (
    InferenceServiceError,
    UnknownModelError,
    ModelDisabledError,
    UnsupportedTaskError,
    MissingAdapterError,
    CudaOutOfMemoryError,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# Direct AI inference by model string id (e.g. "qwen3_0_6b")
# Use /inference/predict for DB-registered model inference by integer model_id
@router.post(
    "/generate",
    response_model=AIInferenceResponse
)
def generate(request: AIInferenceRequest):

    try:
        result = AIService.generate(
            model_id=request.model_id,
            task_type=request.task_type,
            question=request.question,
            context=request.context,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=request.do_sample,
            seed=request.seed,
        )
        return result

    except UnknownModelError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except ModelDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except UnsupportedTaskError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except MissingAdapterError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    except CudaOutOfMemoryError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    except InferenceServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected AI error: {exc}")