from app.services.model_loader.model_loader import ModelLoader


class InferenceService:

    def __init__(self):
        self.loader = ModelLoader()

    def load_model(
        self,
        model_id: int,
        artifact_path: str,
    ):
        return self.loader.load(
            model_id=model_id,
            artifact_path=artifact_path,
        )

    def unload_model(self):
        return self.loader.unload()

    def predict(
        self,
        prompt: str,
    ):

        if self.loader.model is None:
            raise RuntimeError(
                "No model is currently loaded"
            )

        # Connect to DS inference implementation here.

        return {
            "response": "MODEL_RESPONSE"
        }