import time

from sqlalchemy.orm import Session

from app.ai.inference_adapter.inference_adapter import (
    AIInferenceAdapter,
)

from app.model.model_registry import Model_Registry
from app.core.path_utils import validate_artifact_directory, resolve_artifact_path


INFERENCE_ALLOWED_STATUSES = {
    "READY",
    "DEPLOYED",
    "ACTIVE",
    "EVALUATED",
}


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
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        top_p: float = 0.9,
        do_sample: bool = False,
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

        if raw_target_path:
            validation = validate_artifact_directory(raw_target_path)
            if not validation["is_valid"]:
                raise ValueError(
                    f"Model '{model.model_name}' (ID: {model_id}) artifact directory is invalid or missing on disk: "
                    f"{validation['error_message']}"
                )
            resolved_adapter_str = str(validation["resolved_path"])
            adapter_base_model = validation.get("base_model")

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

        start_time = time.perf_counter()

        result = AIInferenceAdapter.generate(
            model_id=resolved_model_id,
            task_type=actual_task_type,
            question=question,
            context=context,
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
                "device": result.get("device"),
            }

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "fine_tuned": False,
            "task_type": task_type,
            "question": question,
            "context": context,
            "response": str(result),
            "raw_response": str(result),
            "latency_seconds": latency,
            "device": None,
        }