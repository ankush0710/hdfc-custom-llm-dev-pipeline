"""
backend/app/routes/ai_routes/ai_routes.py

Direct AI inference route handlers for string model identifiers (e.g. "qwen3_0_6b").
Dispatches inference to the dedicated ML Service worker via AIService/MLClient.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth_dependency import require_permission
from app.model.user_model import User_Model
from app.schema.ai_schema.ai_schema import (
    AIInferenceRequest,
    AIInferenceResponse,
)
from app.services.ai_service.ai_service import AIService

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/generate",
    response_model=AIInferenceResponse
)
def generate(
    request: AIInferenceRequest,
    current_user: User_Model = Depends(require_permission("inference:execute")),
):
    """
    Direct AI inference by model string ID.
    Requires authenticated user with 'inference:execute' permission.
    Calls dedicated ML Service worker.
    """
    return AIService.generate(
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