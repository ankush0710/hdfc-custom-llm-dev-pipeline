"""
backend/app/services/ai_service/ai_service.py

Service for direct AI model inference.
Dispatches requests to the dedicated ML Service via MLClient.
"""
from typing import Any, Dict, List, Optional
from app.clients.ml_client import MLClient


class AIService:

    @staticmethod
    def list_models() -> List[Dict[str, Any]]:
        return MLClient.list_models()

    @staticmethod
    def generate(
        model_id: str,
        task_type: str,
        question: str,
        context: Optional[str] = None,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        top_p: float = 0.9,
        do_sample: bool = False,
        seed: int = 42,
    ) -> Dict[str, Any]:
        return MLClient.generate(
            model_id=model_id,
            task_type=task_type,
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
        )

    @staticmethod
    def unload_model() -> Dict[str, Any]:
        return MLClient.unload_model()