"""
backend/app/clients/ml_client.py

HTTP client for communicating between the FastAPI control plane and the dedicated ML Service.
Provides authenticated, resilient communication with the ML worker.
"""
import logging
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
    def _headers(cls) -> Dict[str, str]:
        return {
            "X-ML-Service-Key": ML_SERVICE_API_KEY,
            "Content-Type": "application/json",
        }

    @classmethod
    def _handle_request_error(cls, exc: Exception, action: str) -> None:
        """Log and map network/HTTP errors to clean API exceptions."""
        if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
            logger.error("ML Service is unreachable at %s for action '%s': %s", ML_SERVICE_URL, action, exc)
            raise HTTPException(
                status_code=503,
                detail=(
                    f"ML Service is currently unavailable at '{ML_SERVICE_URL}'. "
                    f"Please ensure the ML service worker is running and ML_SERVICE_URL is configured."
                ),
            )
        elif isinstance(exc, httpx.ReadTimeout):
            logger.error("ML Service timed out during '%s' after %s seconds", action, ML_SERVICE_TIMEOUT_SECONDS)
            raise HTTPException(
                status_code=504,
                detail=f"ML Service request timed out during '{action}'. The model may still be initializing or computing.",
            )
        elif isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            try:
                err_data = exc.response.json()
                detail = err_data.get("detail", exc.response.text)
            except Exception:
                detail = exc.response.text or str(exc)
            logger.error("ML Service returned HTTP %d for '%s': %s", status, action, detail)
            raise HTTPException(status_code=status, detail=detail)
        else:
            logger.exception("Unexpected error communicating with ML Service for '%s': %s", action, exc)
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
    ) -> Dict[str, Any]:
        """Call ML Service to execute model inference for a registered model ID."""
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
        try:
            with httpx.Client(timeout=ML_SERVICE_TIMEOUT_SECONDS) as client:
                resp = client.post(url, json=payload, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, f"predict(model_id={model_id})")

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
    ) -> Dict[str, Any]:
        """Direct inference by string model identifier (e.g. 'qwen3_0_6b')."""
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
        try:
            with httpx.Client(timeout=ML_SERVICE_TIMEOUT_SECONDS) as client:
                resp = client.post(url, json=payload, headers=cls._headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            cls._handle_request_error(exc, f"generate(model_id={model_id})")

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
