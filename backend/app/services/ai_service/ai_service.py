from app.ai.inference_adapter.inference_adapter import AIInferenceAdapter


class AIService:

    @staticmethod
    def list_models():
        return AIInferenceAdapter.list_models()

    @staticmethod
    def generate(
        model_id: str,
        task_type: str,
        question: str,
        context: str | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        top_p: float = 0.9,
        do_sample: bool = False,
        seed: int = 42,
    ):

        return AIInferenceAdapter.generate(
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
    def unload_model():
        return AIInferenceAdapter.unload()