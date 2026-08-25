from typing import Any

from app.ai.inference_adapter.inference_adapter import (
    AIInferenceAdapter,
)


class ModelLoader:

    def __init__(self):

        self.loaded_model_id: int | None = None

        self.loaded_model_name: str | None = None

    def register_runtime_model(
        self,
        model_id: int,
        model_name: str,
    ) -> dict[str, Any]:

        models = AIInferenceAdapter.list_models()

        ai_model = next(
            (
                model
                for model in models
                if model.get("id") == model_name
            ),
            None,
        )

        if ai_model is None:

            raise RuntimeError(
                f"AI model '{model_name}' "
                "was not found in AI registry."
            )

        self.loaded_model_id = model_id
        self.loaded_model_name = model_name

        return {
            "model_id": model_id,
            "model_name": model_name,
            "status": "READY_FOR_INFERENCE",
            "ai_model": ai_model,
        }

    def unload(self):

        result = AIInferenceAdapter.unload()

        self.loaded_model_id = None
        self.loaded_model_name = None

        return result

    def is_loaded(
        self,
        model_id: int,
    ) -> bool:

        return self.loaded_model_id == model_id