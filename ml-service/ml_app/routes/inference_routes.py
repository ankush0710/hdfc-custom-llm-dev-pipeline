"""
ml-service/app/routes/inference_routes.py

Inference routes hosted on the dedicated ML Service.
Executes actual model loading, LoRA adapter attachment, tokenization, and forward passes.
Protected by verify_ml_service_key.
"""
import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from ..core.security import verify_ml_service_key

from ai.inference.guardrails import BankingDomainGuardrail
from ai.inference.service import (
    run_model,
    get_available_models,
    unload_model,
    SUPPORTED_TASKS,
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

# Architecture constraint: ML Service runs as a single Uvicorn process worker (--workers 1)
# on a dedicated GPU host. A process-level lock serializes inference execution across concurrent
# worker threads to protect the active loaded model cache (_active) and prevent concurrent
# PyTorch execution or CUDA out-of-memory crashes.
_inference_lock = threading.Lock()


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

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        if v not in SUPPORTED_TASKS:
            raise ValueError(
                f"The selected task type '{v}' is not supported. "
                f"Supported task types: {', '.join(sorted(SUPPORTED_TASKS))}"
            )
        return v


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

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        if v not in SUPPORTED_TASKS:
            raise ValueError(
                f"The selected task type '{v}' is not supported. "
                f"Supported task types: {', '.join(sorted(SUPPORTED_TASKS))}"
            )
        return v


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
    # Synchronize with inference lock so we don't evict a model mid-generation
    acquired = _inference_lock.acquire(timeout=10.0)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The inference service is temporarily busy. Cannot unload model during active generation.",
            headers={"Retry-After": "3"},
        )
    try:
        return unload_model()
    except Exception as exc:
        logger.exception("Failed to unload model: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        _inference_lock.release()


@router.post("/generate")
def generate_direct(payload: DirectGenerateRequest, request: Request):
    """Direct inference by string model identifier with controlled concurrency protection."""
    request_id = request.headers.get("X-Request-ID") or "unknown"
    start_time = time.perf_counter()
    logger.info(
        "INFERENCE_REQUEST_RECEIVED request_id=%s model_id=%s task_type=%s",
        request_id, payload.model_id, payload.task_type
    )

    # Pre-generation guardrail validation: reject non-banking queries before acquiring lock or dispatching ML
    guard_result = BankingDomainGuardrail.validate_query(payload.question)
    if not guard_result.is_valid_banking_query:
        refusal_msg = guard_result.refusal_message or "I can only assist with banking and financial-services related queries."
        logger.info("Guardrail rejected non-banking query in ml-service generate_direct: '%s'", payload.question[:80])
        return {
            "model_id": payload.model_id,
            "model_name": payload.model_id,
            "fine_tuned": False,
            "task_type": payload.task_type,
            "question": payload.question,
            "context": payload.context,
            "response": refusal_msg,
            "raw_response": refusal_msg,
            "latency_seconds": 0.001,
            "tokens_generated": 0,
            "device": "guardrail",
            "guardrail_rejected": True,
        }

    acquired = _inference_lock.acquire(timeout=10.0)
    if not acquired:
        logger.warning(
            "INFERENCE_CONCURRENCY_LIMIT request_id=%s model_id=%s worker busy",
            request_id, payload.model_id
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The inference service is temporarily busy handling other requests. Please try again in a few seconds.",
            headers={"Retry-After": "3"},
        )

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
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "INFERENCE_RESPONSE request_id=%s status_code=200 duration_ms=%.2f",
            request_id, duration_ms
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
        logger.exception("Inference error in generate_direct (request_id=%s): %s", request_id, exc)
        raise HTTPException(status_code=500, detail="Unable to generate a response due to a server error.")
    finally:
        _inference_lock.release()


@router.post("/predict")
def predict_registered(payload: PredictModelRequest, request: Request):
    """
    Execute inference for a registered model ID with controlled concurrency protection.
    Handles adapter overrides and model weight resolution.
    """
    request_id = request.headers.get("X-Request-ID") or "unknown"
    start_time = time.perf_counter()
    logger.info(
        "INFERENCE_REQUEST_RECEIVED request_id=%s model_id=%s task_type=%s",
        request_id, payload.model_id, payload.task_type
    )

    # Pre-generation guardrail validation: reject non-banking queries before acquiring lock or dispatching ML
    guard_result = BankingDomainGuardrail.validate_query(payload.question)
    if not guard_result.is_valid_banking_query:
        refusal_msg = guard_result.refusal_message or "I can only assist with banking and financial-services related queries."
        logger.info("Guardrail rejected non-banking query in ml-service predict_registered: '%s'", payload.question[:80])
        return {
            "model_id": payload.model_id,
            "model_name": f"Model #{payload.model_id}",
            "fine_tuned": False,
            "task_type": payload.task_type,
            "question": payload.question,
            "context": payload.context,
            "response": refusal_msg,
            "raw_response": refusal_msg,
            "latency_seconds": 0.001,
            "tokens_generated": 0,
            "device": "guardrail",
            "guardrail_rejected": True,
        }

    acquired = _inference_lock.acquire(timeout=10.0)
    if not acquired:
        logger.warning(
            "INFERENCE_CONCURRENCY_LIMIT request_id=%s model_id=%s worker busy",
            request_id, payload.model_id
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The inference service is temporarily busy handling other requests. Please try again in a few seconds.",
            headers={"Retry-After": "3"},
        )

    try:
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
        duration_ms = round(latency * 1000, 2)
        logger.info(
            "INFERENCE_RESPONSE request_id=%s status_code=200 duration_ms=%.2f",
            request_id, duration_ms
        )

        # Normalize response
        if isinstance(result, dict):
            resp_text = result.get("response", result.get("text", str(result)))
            if isinstance(resp_text, str) and "</think>" in resp_text:
                post_think = resp_text.split("</think>")[-1].strip()
                if post_think:
                    resp_text = post_think
                else:
                    cleaned = re.sub(r"<think>.*?</think>", "", resp_text, flags=re.DOTALL).strip()
                    resp_text = cleaned if cleaned else re.sub(r"</?think>", "", resp_text).strip()

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
                "latency_seconds": round(latency, 4),
                "tokens_generated": tokens_count,
                "device": result.get("device"),
            }

        resp_str = str(result)
        if "</think>" in resp_str:
            post_think = resp_str.split("</think>")[-1].strip()
            if post_think:
                resp_str = post_think
            else:
                cleaned = re.sub(r"<think>.*?</think>", "", resp_str, flags=re.DOTALL).strip()
                resp_str = cleaned if cleaned else re.sub(r"</?think>", "", resp_str).strip()

        return {
            "model_id": payload.model_id,
            "model_name": f"Model #{payload.model_id}",
            "fine_tuned": False,
            "task_type": payload.task_type,
            "question": payload.question,
            "context": payload.context,
            "response": resp_str,
            "raw_response": str(result),
            "latency_seconds": round(latency, 4),
            "tokens_generated": len(resp_str.split()),
            "device": None,
        }

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
        logger.exception("Inference error in predict_registered (request_id=%s): %s", request_id, exc)
        raise HTTPException(status_code=500, detail="Unable to generate a response due to a server error.")
    finally:
        _inference_lock.release()
