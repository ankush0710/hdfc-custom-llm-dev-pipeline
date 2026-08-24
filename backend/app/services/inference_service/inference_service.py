from typing import Union
from sqlalchemy.orm import Session

from app.ai.inference_adapter.inference_adapter import (
    AIInferenceAdapter,
)

from app.model.model_registry import Model_Registry


class InferenceService:

    def __init__(self, db: Session):
        self.db = db

    def predict(
        self,
        model_id: Union[int, str],
        task_type: str,
        question: str,
        context: str | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        top_p: float = 0.9,
        do_sample: bool = False,
        seed: int = 42,
    ):
        target_model_key = None

        # Check if model_id is a database integer ID or numeric string
        if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
            model = (
                self.db.query(Model_Registry)
                .filter(Model_Registry.id == int(model_id))
                .first()
            )

            if not model:
                raise ValueError(f"Model with id {model_id} not found in model registry")

            if model.status != "READY":
                raise ValueError(
                    f"Model '{model.model_name}' version '{model.version}' is not READY. "
                    f"Current status: {model.status}"
                )

            # Map database model metadata to AI service runtime model key
            name_combined = f"{model.model_name} {model.base_model}".lower()
            if "1.5" in name_combined and "qwen" in name_combined:
                target_model_key = "qwen2_5_1_5b_instruct"
            elif "smol" in name_combined:
                target_model_key = "smollm2_1_7b_instruct"
            elif "qwen" in name_combined:
                target_model_key = "qwen3_0_6b"
            else:
                target_model_key = model.model_name
        else:
            target_model_key = str(model_id)

        result = AIInferenceAdapter.generate(
            model_id=target_model_key,
            task_type=task_type,
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
        )

        return result