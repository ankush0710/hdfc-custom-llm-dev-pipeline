from pathlib import Path
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "ai" / "config" / "model_registry.yaml"


def load_model_registry():
    """Load and validate the project's model candidate registry."""

    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Model registry not found: {REGISTRY_PATH}"
        )

    with REGISTRY_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not config or "models" not in config:
        raise ValueError(
            "Model registry must contain a top-level 'models' key."
        )

    models = config["models"]

    if not isinstance(models, list) or not models:
        raise ValueError(
            "Model registry must contain at least one model."
        )

    required_fields = {
        "id",
        "name",
        "family",
        "parameters_billions",
        "license",
        "priority",
        "enabled",
    }

    for model in models:
        missing = required_fields - model.keys()

        if missing:
            raise ValueError(
                f"Model '{model.get('id', '<unknown>')}' "
                f"is missing fields: {sorted(missing)}"
            )

    return models


if __name__ == "__main__":
    models = load_model_registry()

    print("\n=== MODEL CANDIDATE REGISTRY ===")

    for model in models:
        print(
            f"{model['priority']}. "
            f"{model['id']} | "
            f"{model['parameters_billions']}B | "
            f"{model['license']}"
        )