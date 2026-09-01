
import logging
import os
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.inference_adapter.inference_adapter import (
    AIInferenceAdapter,
)

from app.model.model_registry import Model_Registry
from app.core.path_utils import validate_artifact_directory, resolve_artifact_path

logger = logging.getLogger(__name__)

INFERENCE_ALLOWED_STATUSES = {
    "READY",
    "DEPLOYED",
    "ACTIVE",
    "EVALUATED",
}

# Module-level cache to remember resolved artifact paths across requests
_RESOLVED_ADAPTER_PATHS: dict[int, str] = {}


class InferenceService:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

    def predict(
        self,
        model_id: int,
        task_type: str,
        question: str,
        context: str | None = None,
        max_new_tokens: int = int(os.getenv("AI_MAX_NEW_TOKENS", "256")),
        temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7")),
        top_p: float = float(os.getenv("AI_TOP_P", "0.9")),
        do_sample: bool = os.getenv("AI_DO_SAMPLE", "true").lower() == "true",
        seed: int = 42,
    ):

        # ---------------------------------------
        # 1. Find model in PostgreSQL
        # ---------------------------------------
        model = (
            self.db.query(Model_Registry)
            .filter(
                Model_Registry.id == model_id
            )
            .first()
        )

        if model is None:
            raise ValueError(
                f"Model ID '{model_id}' was not found in the Model Registry."
            )

        # ---------------------------------------
        # 2. Check model status
        # ---------------------------------------
        if model.status not in INFERENCE_ALLOWED_STATUSES:
            raise ValueError(
                f"Model '{model.model_name}' (v{model.version}) has status '{model.status}'. "
                f"Inference is only allowed for models with status in {sorted(INFERENCE_ALLOWED_STATUSES)}."
            )

        # ---------------------------------------
        # 3. Validate & resolve artifact path on disk
        # ---------------------------------------
        raw_target_path = model.adapter_path or model.artifact_path
        resolved_adapter_str = None
        adapter_base_model = None

        # Check process-level cache first to avoid re-resolving or downloading
        if model_id in _RESOLVED_ADAPTER_PATHS:
            cached_str = _RESOLVED_ADAPTER_PATHS[model_id]
            if Path(cached_str).is_dir():
                v = validate_artifact_directory(cached_str)
                if v["is_valid"]:
                    resolved_adapter_str = str(v["resolved_path"])
                    adapter_base_model = v.get("base_model")

        if not resolved_adapter_str and raw_target_path:
            validation = validate_artifact_directory(raw_target_path)

            # If not resolved locally, check if local training run artifact directory exists
            if not validation["is_valid"] and model.training_job_id:
                try:
                    from app.model.training_job_model import TrainingJobModel
                    job = self.db.query(TrainingJobModel).filter(TrainingJobModel.id == model.training_job_id).first()
                    if job and job.training_run_id:
                        from app.core.config import HF_LOCAL_TEMP_DIR
                        run_dir = Path(HF_LOCAL_TEMP_DIR) / "runs" / f"run_{job.training_run_id}"
                        if run_dir.exists():
                            validation = validate_artifact_directory(run_dir)
                except Exception as lookup_err:
                    logger.warning("Error checking local run directory for model %d: %s", model_id, lookup_err)

            # If still not resolved, attempt to download model artifacts from Hugging Face Hub (once)
            if not validation["is_valid"] and (model.huggingface_path or raw_target_path.startswith("models/")):
                try:
                    from app.services.huggingface_service.hf_storage_service import get_hf_storage_service
                    hf_service = get_hf_storage_service()
                    target_hf_path = model.huggingface_path or raw_target_path
                    downloaded_dir = hf_service.download_model(path_in_repo=target_hf_path)
                    validation = validate_artifact_directory(downloaded_dir)
                except Exception as dl_err:
                    logger.warning("Failed to download model %d from HF Hub: %s", model_id, dl_err)

            if not validation["is_valid"]:
                raise ValueError(
                    f"Model '{model.model_name}' (ID: {model_id}) artifact directory is invalid or missing on disk: "
                    f"{validation['error_message']}"
                )
            resolved_adapter_str = str(validation["resolved_path"])
            adapter_base_model = validation.get("base_model")
            _RESOLVED_ADAPTER_PATHS[model_id] = resolved_adapter_str

        # ---------------------------------------
        # 4. Resolve Base Model Architecture
        # ---------------------------------------
        raw_base = adapter_base_model or (model.base_model or "").strip()
        if not raw_base or raw_base.lower() in {"base_model", "none", "null"}:
            raw_base = "Qwen/Qwen3-0.6B"

        base_slug = raw_base.split("/")[-1].lower().replace("-", "_").replace(".", "_")

        # Map known base_model slugs to AI service model IDs
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

        # ---------------------------------------
        # 5. Call AI inference
        # ---------------------------------------
        valid_tasks = {
            "intent_classification",
            "sft_grounded_generation",
            "customer_faq_qa",
            "domain_concept_qa",
            "inference",
        }
        actual_task_type = task_type if task_type in valid_tasks and task_type != "inference" else "sft_grounded_generation"

        # Sanitize context: if context is a system role instruction (e.g. "You are an expert..."),
        # do not format it as factual banking context
        clean_context = context
        if clean_context and isinstance(clean_context, str):
            c_str = clean_context.strip()
            if c_str.lower().startswith("you are ") or "compliance ai" in c_str.lower() or "fraud analysis" in c_str.lower():
                clean_context = None

        start_time = time.perf_counter()

        result = AIInferenceAdapter.generate(
            model_id=resolved_model_id,
            task_type=actual_task_type,
            question=question,
            context=clean_context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
            adapter_path_override=resolved_adapter_str,
            base_model_override=raw_base,
        )

        latency = (
            time.perf_counter()
            - start_time
        )

        # ---------------------------------------
        # 5. Normalize response
        # ---------------------------------------

        if isinstance(result, dict):
            response_text = result.get(
                "response",
                result.get(
                    "text",
                    str(result),
                ),
            )
            if isinstance(response_text, str) and "</think>" in response_text:
                response_text = response_text.split("</think>")[-1].strip()

            tokens_count = result.get("tokens_generated")
            if tokens_count is None and isinstance(response_text, str):
                tokens_count = len(response_text.split())

            return {
                "model_id": model.id,
                "model_name": model.model_name,
                "fine_tuned": result.get("fine_tuned", False),
                "task_type": task_type,
                "question": question,
                "context": context,
                "response": response_text,
                "raw_response": str(result),
                "latency_seconds": latency,
                "tokens_generated": tokens_count,
                "device": result.get("device"),
            }

        response_str = str(result)
        if "</think>" in response_str:
            response_str = response_str.split("</think>")[-1].strip()

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "fine_tuned": False,
            "task_type": task_type,
            "question": question,
            "context": context,
            "response": response_str,
            "raw_response": str(result),
            "latency_seconds": latency,
            "tokens_generated": len(response_str.split()),
            "device": None,
        }