"""
backend/app/clients/ml_client.py

HTTP client for communicating between the FastAPI control plane and the dedicated ML Service.
Provides authenticated, resilient communication with the ML worker.
"""
import logging
import random
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from app.core.config import (
    ML_SERVICE_API_KEY,
    ML_SERVICE_TIMEOUT_SECONDS,
    ML_SERVICE_URL,
)

logger = logging.getLogger(__name__)



class MLServiceClientError(HTTPException):
    """Exception raised when communication with ML service fails."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class MLClient:
    """Client for dispatching heavy ML workloads (inference, training, evaluation) to ML Service."""

    @classmethod
    def _headers(cls, request_id: Optional[str] = None) -> Dict[str, str]:
        headers = {

            "X-ML-Service-Key": ML_SERVICE_API_KEY,
            "Content-Type": "application/json",
            
        }
        if request_id:
            headers["X-Request-ID"] = request_id
        return headers

    @classmethod
    def _handle_request_error(cls, exc: Exception, action: str, request_id: Optional[str] = None) -> None:
        """Log and map network/HTTP errors to clean API exceptions."""
        req_ctx = f" request_id={request_id}" if request_id else ""
        if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
            logger.error("ML Service is unreachable at %s for action '%s'%s: %s", ML_SERVICE_URL, action, req_ctx, exc)
            raise HTTPException(
                status_code=503,
                detail="The model service is currently unavailable. Please try again shortly.",
            )
        elif isinstance(exc, httpx.ReadTimeout):
            logger.error("ML Service timed out during '%s'%s after %s seconds", action, req_ctx, ML_SERVICE_TIMEOUT_SECONDS)
            raise HTTPException(
                status_code=504,
                detail="Inference request timed out. The model may still be initializing.",
            )
        elif isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            try:
                err_data = exc.response.json()
                detail = err_data.get("detail", exc.response.text)
            except Exception:
                detail = exc.response.text or str(exc)
            
            response_headers = {}
            if status == 429:
                detail = "The inference service is temporarily busy. Please try again in a few seconds."
                retry_after = exc.response.headers.get("Retry-After")
                if retry_after:
                    response_headers["Retry-After"] = retry_after
            elif status == 503 and not detail:
                detail = "The model service is currently unavailable. Please try again shortly."
            
            logger.warning("ML Service returned HTTP %d for '%s'%s: %s", status, action, req_ctx, detail)
            raise HTTPException(status_code=status, detail=detail, headers=response_headers or None)
        else:
            logger.exception("Unexpected error communicating with ML Service for '%s'%s: %s", action, req_ctx, exc)
            raise HTTPException(status_code=502, detail=f"Failed to communicate with ML Service: {str(exc)}")

    # ─────────────────────────── Health Check ─────────────────────────── #

    @classmethod
    def health(cls) -> Dict[str, Any]:
        """Check if ML Service is reachable and healthy."""
        url = f"{ML_SERVICE_URL}/health"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, "health_check")

    # ─────────────────────────── Inference APIs ───────────────────────── #

    @classmethod
    def predict(
        cls,
        model_id: int,
        task_type: str,
        question: str,
        context: Optional[str] = None,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        seed: int = 42,
        adapter_path_override: Optional[str] = None,
        base_model_override: Optional[str] = None,
        huggingface_path: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call ML Service to execute model inference for a registered model ID with bounded retry on transient 429/503."""
        url = f"{ML_SERVICE_URL}/api/v1/inference/predict"
        payload = {
            "model_id": model_id,
            "task_type": task_type,
            "question": question,
            "context": context,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": do_sample,
            "seed": seed,
            "adapter_path_override": adapter_path_override,
            "base_model_override": base_model_override,
            "huggingface_path": huggingface_path,
        }
        max_retries = 3
        backoff = 1.5
        for attempt in range(max_retries):
            logger.info(
                "INFERENCE_UPSTREAM_REQUEST request_id=%s url=%s attempt=%d/%d model_id=%s",
                request_id, url, attempt + 1, max_retries, model_id
            )
            try:
                with httpx.Client(timeout=ML_SERVICE_TIMEOUT_SECONDS) as client:
                    resp = client.post(url, json=payload, headers=cls._headers(request_id=request_id))
                    if resp.status_code in (429, 503) and attempt < max_retries - 1:
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after and retry_after.strip().isdigit():
                            delay = min(max(float(retry_after), 1.0), 10.0)
                        else:
                            delay = min(backoff + random.uniform(0.1, 0.4), 10.0)
                        logger.warning(
                            "INFERENCE_UPSTREAM_RETRY request_id=%s status=%d attempt=%d/%d retrying in %.2fs...",
                            request_id, resp.status_code, attempt + 1, max_retries, delay
                        )
                        time.sleep(delay)
                        backoff = min(backoff * 2.0, 8.0)
                        continue
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (429, 503) and attempt < max_retries - 1:
                    delay = min(backoff + random.uniform(0.1, 0.4), 10.0)
                    time.sleep(delay)
                    backoff = min(backoff * 2.0, 8.0)
                    continue
                cls._handle_request_error(exc, f"predict(model_id={model_id})", request_id=request_id)
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                if attempt < max_retries - 1:
                    delay = min(backoff + random.uniform(0.1, 0.4), 10.0)
                    time.sleep(delay)
                    backoff = min(backoff * 2.0, 8.0)
                    continue
                cls._handle_request_error(exc, f"predict(model_id={model_id})", request_id=request_id)
            except Exception as exc:
                cls._handle_request_error(exc, f"predict(model_id={model_id})", request_id=request_id)

    @classmethod
    def generate(
        cls,
        model_id: str,
        task_type: str,
        question: str,
        context: Optional[str] = None,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        top_p: float = 0.9,
        do_sample: bool = False,
        seed: int = 42,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Direct inference by string model identifier (e.g. 'qwen3_0_6b') with bounded retry on transient 429/503."""
        url = f"{ML_SERVICE_URL}/api/v1/inference/generate"
        payload = {
            "model_id": model_id,
            "task_type": task_type,
            "question": question,
            "context": context,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": do_sample,
            "seed": seed,
        }
        max_retries = 3
        backoff = 1.5
        for attempt in range(max_retries):
            logger.info(
                "INFERENCE_UPSTREAM_REQUEST request_id=%s url=%s attempt=%d/%d model_id=%s",
                request_id, url, attempt + 1, max_retries, model_id
            )
            try:
                with httpx.Client(timeout=ML_SERVICE_TIMEOUT_SECONDS) as client:
                    resp = client.post(url, json=payload, headers=cls._headers(request_id=request_id))
                    if resp.status_code in (429, 503) and attempt < max_retries - 1:
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after and retry_after.strip().isdigit():
                            delay = min(max(float(retry_after), 1.0), 10.0)
                        else:
                            delay = min(backoff + random.uniform(0.1, 0.4), 10.0)
                        logger.warning(
                            "INFERENCE_UPSTREAM_RETRY request_id=%s status=%d attempt=%d/%d retrying in %.2fs...",
                            request_id, resp.status_code, attempt + 1, max_retries, delay
                        )
                        time.sleep(delay)
                        backoff = min(backoff * 2.0, 8.0)
                        continue
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (429, 503) and attempt < max_retries - 1:
                    delay = min(backoff + random.uniform(0.1, 0.4), 10.0)
                    time.sleep(delay)
                    backoff = min(backoff * 2.0, 8.0)
                    continue
                cls._handle_request_error(exc, f"generate(model_id={model_id})", request_id=request_id)
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                if attempt < max_retries - 1:
                    delay = min(backoff + random.uniform(0.1, 0.4), 10.0)
                    time.sleep(delay)
                    backoff = min(backoff * 2.0, 8.0)
                    continue
                cls._handle_request_error(exc, f"generate(model_id={model_id})", request_id=request_id)
            except Exception as exc:
                cls._handle_request_error(exc, f"generate(model_id={model_id})", request_id=request_id)

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """Query ML Service for available models."""
        url = f"{ML_SERVICE_URL}/api/v1/inference/models"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, "list_models")

    @classmethod
    def unload_model(cls) -> Dict[str, Any]:
        """Instruct ML Service to evict the active cached model from memory."""
        url = f"{ML_SERVICE_URL}/api/v1/inference/unload"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, "unload_model")

    # ─────────────────────────── Training APIs ────────────────────────── #

    @classmethod
    def dispatch_training(
        cls,
        run_id: int,
        base_model: str,
        dataset_version_id: int,
        epochs: float,
        learning_rate: float,
        batch_size: int,
        training_method: str = "lora",
    ) -> Dict[str, Any]:
        """
        Dispatch asynchronous training job to the ML service worker.
        Returns immediate acknowledgment without blocking HTTP request.
        """
        url = f"{ML_SERVICE_URL}/api/v1/training/dispatch"
        payload = {
            "run_id": run_id,
            "base_model": base_model,
            "dataset_version_id": dataset_version_id,
            "epochs": epochs,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "training_method": training_method,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, f"dispatch_training(run_id={run_id})")

    @classmethod
    def stop_training(cls, run_id: int) -> Dict[str, Any]:
        """Notify ML Service to abort an in-progress training run."""
        url = f"{ML_SERVICE_URL}/api/v1/training/stop/{run_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("ML Service stop_training notification error for run %d: %s", run_id, exc)
            return {"status": "stop_requested", "warning": str(exc)}

    # ─────────────────────────── Evaluation APIs ──────────────────────── #

    @classmethod
    def dispatch_evaluation(
        cls,
        evaluation_id: int,
        run_id: int,
        model_id: int,
        test_dataset_id: int,
    ) -> Dict[str, Any]:
        """
        Dispatch asynchronous model evaluation job to the ML service worker.
        Returns immediate acknowledgment.
        """
        url = f"{ML_SERVICE_URL}/api/v1/evaluation/dispatch"
        payload = {
            "evaluation_id": evaluation_id,
            "run_id": run_id,
            "model_id": model_id,
            "test_dataset_id": test_dataset_id,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, f"dispatch_evaluation(evaluation_id={evaluation_id})")

    @classmethod
    def stop_evaluation(cls, evaluation_id: int) -> Dict[str, Any]:
        """Notify ML Service to abort an in-progress evaluation run."""
        url = f"{ML_SERVICE_URL}/api/v1/evaluation/stop/{evaluation_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("ML Service stop_evaluation notification error for eval %d: %s", evaluation_id, exc)
            return {"status": "stop_requested", "warning": str(exc)}
