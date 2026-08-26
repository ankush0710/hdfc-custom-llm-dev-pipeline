import time

from sqlalchemy.orm import Session

from app.ai.inference_adapter.inference_adapter import (
    AIInferenceAdapter,
)

from app.model.model_registry import Model_Registry


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
                f"Model with id {model_id} "
                "was not found."
            )

        # ---------------------------------------
        # 2. Check model status
        # ---------------------------------------

        if model.status not in INFERENCE_ALLOWED_STATUSES:

            raise ValueError(
                f"Model '{model.model_name}' "
                f"version '{model.version}' "
                f"is not available for inference. "
                f"Current status: {model.status}"
            )

        # ---------------------------------------
        # 3. Validate model name
        # ---------------------------------------

        if not model.model_name:

            raise ValueError(
                "Model registry does not contain "
                "a model_name."
            )

        # ---------------------------------------
        # 4. Call AI inference
        # ---------------------------------------
        valid_tasks = {
            "intent_classification",
            "sft_grounded_generation",
            "customer_faq_qa",
            "domain_concept_qa",
        }
        actual_task_type = task_type if task_type in valid_tasks else "sft_grounded_generation"

        # Resolve AI model string ID from base_model in the registry.
        # base_model holds the HuggingFace model path (e.g. "Qwen/Qwen3-0.6B").
        # We derive the AI pipeline key from the last path segment, lowercased.
        raw_base = (model.base_model or "").strip()
        # Derive slug: take last path component, lower, replace - with _
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
            # Cannot resolve — raise a real error so the caller knows
            raise ValueError(
                f"Cannot resolve AI model ID for base_model '{raw_base}' "
                f"(registry model: '{model.model_name}'). "
                f"Supported base models: Qwen/Qwen3-0.6B, Qwen/Qwen2.5-1.5B-Instruct, HuggingFaceTB/SmolLM2-1.7B-Instruct."
            )

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
            adapter_path_override=model.adapter_path or None,
            base_model_override=raw_base or "Qwen/Qwen3-0.6B",
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