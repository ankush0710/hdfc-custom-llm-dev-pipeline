from typing import Any

from ai.inference.service import (
    run_model,
    get_available_models,
    unload_model,
)


class AIInferenceAdapter:

    @staticmethod
    def list_models():
        return get_available_models()

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
        adapter_path_override: str | None = None,
        base_model_override: str | None = None,
    ) -> dict[str, Any]:

        return run_model(
            model_id=model_id,
            task_type=task_type,
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            seed=seed,
            adapter_path_override=adapter_path_override,
            base_model_override=base_model_override,
        )

    @staticmethod
    def unload():
        return unload_model()