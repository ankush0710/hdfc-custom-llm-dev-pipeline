"""
backend/app/services/inference_service/inference_service.py

Control plane inference service for registered models.
Validates database model records and dispatches computation to the dedicated ML Service.
Zero torch/transformers dependencies.
"""
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.clients.ml_client import MLClient
from app.core.path_utils import resolve_artifact_path, validate_artifact_directory
from app.model.model_registry import Model_Registry
from app.schema.inference_schema.inference_schema import SUPPORTED_TASK_TYPES

logger = logging.getLogger(__name__)

INFERENCE_ALLOWED_STATUSES = {
    "READY",
    "DEPLOYED",
    "ACTIVE",
    "EVALUATED",
}


class InferenceService:

    def __init__(self, db: Session):
        self.db = db

    def predict(
        self,
        model_id: int,
        task_type: str,
        question: str,
        context: Optional[str] = None,
        max_new_tokens: int = int(os.getenv("AI_MAX_NEW_TOKENS", "256")),
        temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7")),
        top_p: float = float(os.getenv("AI_TOP_P", "0.9")),
        do_sample: bool = os.getenv("AI_DO_SAMPLE", "true").lower() == "true",
        seed: int = 42,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        # 0. Validate task type
        if task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(
                f"The selected task type '{task_type}' is not supported. "
                f"Supported task types: {', '.join(sorted(SUPPORTED_TASK_TYPES))}"
            )

        # 1. Find model in PostgreSQL
        model = (
            self.db.query(Model_Registry)
            .filter(Model_Registry.id == model_id)
            .first()
        )

        if model is None:
            raise ValueError(f"Model ID '{model_id}' was not found in the Model Registry.")

        # 2. Check model status
        if model.status not in INFERENCE_ALLOWED_STATUSES:
            raise ValueError(
                f"Model '{model.model_name}' (v{model.version}) has status '{model.status}'. "
                f"Inference is only allowed for models with status in {sorted(INFERENCE_ALLOWED_STATUSES)}."
            )

        # 3. Resolve metadata
        raw_target_path = model.adapter_path or model.artifact_path
        hf_path = model.huggingface_path

        # 4. Dispatch inference to ML Service via MLClient
        start_time = time.perf_counter()

        ml_result = MLClient.predict(
            model_id=model.id,
            task_type=task_type,
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
            adapter_path_override=raw_target_path,
            base_model_override=model.base_model,
            huggingface_path=hf_path,
            request_id=request_id,
        )

        latency = time.perf_counter() - start_time

        # 5. Format return payload matching existing API contract
        response_text = ml_result.get("response", ml_result.get("text", str(ml_result)))
        tokens_count = ml_result.get("tokens_generated")
        if tokens_count is None and isinstance(response_text, str):
            tokens_count = len(response_text.split())

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "fine_tuned": ml_result.get("fine_tuned", False),
            "task_type": task_type,
            "question": question,
            "context": context,
            "response": response_text,
            "raw_response": str(ml_result),
            "latency_seconds": round(latency, 4),
            "tokens_generated": tokens_count,
            "device": ml_result.get("device"),
        }