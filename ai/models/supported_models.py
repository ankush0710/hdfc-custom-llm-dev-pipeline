"""
ai/models/supported_models.py

Central source of truth for supported base models in the HDFC AI subsystem.
Re-exports configuration from backend.app.constants.supported_models if available,
or provides standalone definition.
"""
from typing import Dict, Any

SUPPORTED_TRAINING_MODELS: Dict[str, Dict[str, Any]] = {
    "qwen2_5_1_5b_instruct": {
        "id": "qwen2_5_1_5b_instruct",
        "display_name": "Qwen 2.5 1.5B Instruct",
        "hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "parameters": "1.54B",
        "architecture": "qwen2",
        "description": "High-accuracy instruction-tuned enterprise model (1.54B parameters)",
    },
    "qwen3_0_6b": {
        "id": "qwen3_0_6b",
        "display_name": "Qwen 3 0.6B",
        "hf_model_id": "Qwen/Qwen3-0.6B",
        "parameters": "0.6B",
        "architecture": "qwen",
        "description": "Ultra-lightweight base model (0.6B parameters) optimized for edge & fast fine-tuning",
    },
    "smollm2_1_7b_instruct": {
        "id": "smollm2_1_7b_instruct",
        "display_name": "SmolLM2 1.7B Instruct",
        "hf_model_id": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
        "parameters": "1.7B",
        "architecture": "llama",
        "description": "High-efficiency compact reasoning model (1.7B parameters)",
    },
}

_MODEL_LOOKUP = {
    "qwen2_5_1_5b_instruct": "qwen2_5_1_5b_instruct",
    "qwen3_0_6b": "qwen3_0_6b",
    "smollm2_1_7b_instruct": "smollm2_1_7b_instruct",
    "qwen/qwen2.5-1.5b-instruct": "qwen2_5_1_5b_instruct",
    "qwen/qwen3-0.6b": "qwen3_0_6b",
    "huggingfacetb/smollm2-1.7b-instruct": "smollm2_1_7b_instruct",
    "qwen2.5-1.5b-instruct": "qwen2_5_1_5b_instruct",
    "qwen-2.5-1.5b-instruct": "qwen2_5_1_5b_instruct",
    "qwen3-0.6b": "qwen3_0_6b",
    "qwen-3-0.6b": "qwen3_0_6b",
    "smollm2-1.7b-instruct": "smollm2_1_7b_instruct",
    "smollm2": "smollm2_1_7b_instruct",
}


def resolve_model_config(model_identifier: str) -> Dict[str, Any]:
    if not model_identifier or not isinstance(model_identifier, str):
        raise ValueError(
            f"Invalid model identifier: '{model_identifier}'. "
            f"Supported models: {list(SUPPORTED_TRAINING_MODELS.keys())}"
        )

    cleaned = model_identifier.strip().lower()
    canonical_key = _MODEL_LOOKUP.get(cleaned)

    if not canonical_key or canonical_key not in SUPPORTED_TRAINING_MODELS:
        raise ValueError(
            f"Unsupported model '{model_identifier}'. "
            f"Only the following 3 models are supported in this pipeline:\n"
            f"  1. 'qwen2_5_1_5b_instruct' (Qwen/Qwen2.5-1.5B-Instruct - 1.54B)\n"
            f"  2. 'qwen3_0_6b' (Qwen/Qwen3-0.6B - 0.6B)\n"
            f"  3. 'smollm2_1_7b_instruct' (HuggingFaceTB/SmolLM2-1.7B-Instruct - 1.7B)"
        )

    return SUPPORTED_TRAINING_MODELS[canonical_key]


def resolve_hf_model_id(model_identifier: str) -> str:
    return resolve_model_config(model_identifier)["hf_model_id"]


def resolve_internal_model_id(model_identifier: str) -> str:
    return resolve_model_config(model_identifier)["id"]
