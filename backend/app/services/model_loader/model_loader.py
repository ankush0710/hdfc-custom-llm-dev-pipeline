from typing import Any


class ModelLoader:

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.loaded_model_id = None

    def load(
        self,
        model_id: int,
        artifact_path: str,
    ):  


        # inference service comes from ai folder to load the model
        from ai.inference.service import load_model

        self.model, self.tokenizer = load_model(
            artifact_path
        )

        self.loaded_model_id = model_id

        return {
            "model_id": model_id,
            "status": "LOADED",
        }

    def unload(self):

        self.model = None
        self.tokenizer = None
        self.loaded_model_id = None

        return {
            "status": "UNLOADED"
        }