from ai.models.registry import load_registry


def test_load_registry_returns_models():
    models = load_registry()

    assert isinstance(models, list)
    assert models

    model_ids = {model["id"] for model in models}

    assert "qwen3_0_6b" in model_ids
    assert "qwen2_5_1_5b_instruct" in model_ids
    assert "smollm2_1_7b_instruct" in model_ids