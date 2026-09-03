"""
backend/app/services/model_loader/model_loader.py

Runtime model state manager for the control plane.
Queries ML Service for available models.
"""
from typing import Any, Optional
from app.clients.ml_client import MLClient


class ModelLoader:

    def __init__(self):
        self.loaded_model_id: Optional[int] = None
        self.loaded_model_name: Optional[str] = None

    def register_runtime_model(
        self,
        model_id: int,
        model_name: str,
    ) -> dict[str, Any]:

        models = MLClient.list_models()

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
                f"AI model '{model_name}' was not found in AI registry."
            )

        self.loaded_model_id = model_id
        self.loaded_model_name = model_name

        return {
            "model_id": model_id,
            "model_name": model_name,
            "status": "ready",
        }

    def unload_runtime_model(self) -> dict[str, Any]:
        result = MLClient.unload_model()
        self.loaded_model_id = None
        self.loaded_model_name = None
        return result

    def get_runtime_status(self) -> dict[str, Any]:
        return {
            "loaded_model_id": self.loaded_model_id,
            "loaded_model_name": self.loaded_model_name,
        }