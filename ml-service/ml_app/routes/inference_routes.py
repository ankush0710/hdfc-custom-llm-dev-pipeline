"""
ml-service/app/routes/inference_routes.py

Inference routes hosted on the dedicated ML Service.
Executes actual model loading, LoRA adapter attachment, tokenization, and forward passes.
Protected by verify_ml_service_key.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.security import verify_ml_service_key

from ai.inference.service import (
    run_model,
    get_available_models,
    unload_model,
    InferenceServiceError,
    UnknownModelError,
    ModelDisabledError,
    UnsupportedTaskError,
    MissingAdapterError,
    CudaOutOfMemoryError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/inference",
    tags=["ML Inference"],
    dependencies=[Depends(verify_ml_service_key)],
)


# ────────────────────────────── Request Schemas ────────────────────────────── #

class DirectGenerateRequest(BaseModel):
    model_id: str
    task_type: str
    question: str
    context: Optional[str] = None
    max_new_tokens: int = 256
    temperature: float = 0.2
    top_p: float = 0.9
    do_sample: bool = False
    seed: int = 42


class PredictModelRequest(BaseModel):
    model_id: int
    task_type: str
    question: str
    context: Optional[str] = None
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    do_sample: bool = True
    seed: int = 42
    adapter_path_override: Optional[str] = None
    base_model_override: Optional[str] = None
    huggingface_path: Optional[str] = None


# ──────────────────────────────── Endpoints ────────────────────────────────── #

@router.get("/models")
def list_available_models():
    """List all foundation and fine-tuned models registered in the inference service."""
    try:
        return get_available_models()
    except Exception as exc:
        logger.exception("Failed to retrieve available models: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/unload")
def evict_cached_model():
    """Unload the active model from GPU/RAM to free up system memory."""
    try:
        return unload_model()
    except Exception as exc:
        logger.exception("Failed to unload model: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate")
def generate_direct(payload: DirectGenerateRequest):
    """Direct inference by string model identifier."""
    try:
        result = run_model(
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
        raise HTTPException(status_code=507, detail=str(exc))
    except Exception as exc:
        logger.exception("Inference error in generate_direct: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/predict")
def predict_registered(payload: PredictModelRequest):
    """
    Execute inference for a registered model ID.
    Handles adapter overrides and model weight resolution.
    """
    try:
        start_time = time.perf_counter()

        # Resolve model slug
        raw_base = payload.base_model_override or "Qwen/Qwen3-0.6B"
        base_slug = raw_base.split("/")[-1].lower().replace("-", "_").replace(".", "_")

        known_model_ids = {"qwen3_0_6b", "qwen2_5_1_5b_instruct", "smollm2_1_7b_instruct"}
        if base_slug in known_model_ids:
            resolved_model_id = base_slug
        elif "qwen3" in base_slug:
            resolved_model_id = "qwen3_0_6b"
        elif "qwen2" in base_slug or "qwen" in base_slug:
            resolved_model_id = "qwen2_5_1_5b_instruct"
        elif "smol" in base_slug:
            resolved_model_id = "smollm2_1_7b_instruct"
        else:
            resolved_model_id = "qwen3_0_6b"

        # Sanitize system context if needed
        clean_context = payload.context
        if clean_context and isinstance(clean_context, str):
            c_str = clean_context.strip().lower()
            if c_str.startswith("you are ") or "compliance ai" in c_str or "fraud analysis" in c_str:
                clean_context = None

        result = run_model(
            model_id=resolved_model_id,
            task_type=payload.task_type,
            question=payload.question,
            context=clean_context,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
            do_sample=payload.do_sample,
            seed=payload.seed,
            adapter_path_override=payload.adapter_path_override,
            base_model_override=payload.base_model_override,
        )

        latency = time.perf_counter() - start_time

        # Normalize response
        if isinstance(result, dict):
            resp_text = result.get("response", result.get("text", str(result)))
            if isinstance(resp_text, str) and "</think>" in resp_text:
                resp_text = resp_text.split("</think>")[-1].strip()

            tokens_count = result.get("tokens_generated")
            if tokens_count is None and isinstance(resp_text, str):
                tokens_count = len(resp_text.split())

            return {
                "model_id": payload.model_id,
                "model_name": f"Model #{payload.model_id}",
                "fine_tuned": result.get("fine_tuned", False),
                "task_type": payload.task_type,
                "question": payload.question,
                "context": payload.context,
                "response": resp_text,
                "raw_response": str(result),
                "latency_seconds": latency,
                "tokens_generated": tokens_count,
                "device": result.get("device"),
            }

        resp_str = str(result)
        if "</think>" in resp_str:
            resp_str = resp_str.split("</think>")[-1].strip()

        return {
            "model_id": payload.model_id,
            "model_name": f"Model #{payload.model_id}",
            "fine_tuned": False,
            "task_type": payload.task_type,
            "question": payload.question,
            "context": payload.context,
            "response": resp_str,
            "raw_response": str(result),
            "latency_seconds": latency,
            "tokens_generated": len(resp_str.split()),
            "device": None,
        }

    except UnknownModelError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except MissingAdapterError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except CudaOutOfMemoryError as exc:
        raise HTTPException(status_code=507, detail=str(exc))
    except Exception as exc:
        logger.exception("Inference error in predict_registered: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
