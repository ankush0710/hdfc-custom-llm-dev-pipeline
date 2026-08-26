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

        start_time = time.perf_counter()

        result = AIInferenceAdapter.generate(
            model_id=model.model_name,
            task_type=task_type,
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
            adapter_path_override=model.adapter_path or None,
            base_model_override=model.base_model or None,
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