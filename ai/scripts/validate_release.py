from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = ROOT / "ai" / "manifests" / "model_release.json"
REGISTRY_PATH = ROOT / "ai" / "config" / "model_registry.yaml"
MODEL_CONFIG_PATH = ROOT / "ai" / "config" / "model_config.yaml"
ARTIFACT_DIR = ROOT / "ai" / "artifacts" / "full_training"


def check(condition: bool, label: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"{label}: {status}")
    return condition


def main() -> int:
    print("AI RELEASE VALIDATION")
    print("=" * 40)

    all_passed = True

    all_passed &= check(MANIFEST_PATH.is_file(), "Release manifest")

    if MANIFEST_PATH.is_file():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            all_passed &= check(
                manifest.get("base_model") == "Qwen/Qwen3-0.6B",
                "Base model",
            )
            all_passed &= check(
                manifest.get("dataset_release") == "Release A",
                "Dataset release",
            )
        except json.JSONDecodeError as exc:
            print(f"Release manifest JSON: FAIL ({exc})")
            all_passed = False

    all_passed &= check(REGISTRY_PATH.is_file(), "Model registry")
    all_passed &= check(MODEL_CONFIG_PATH.is_file(), "Model configuration")
    all_passed &= check(ARTIFACT_DIR.is_dir(), "LoRA artifact directory")

    required_artifacts = [
        "adapter_config.json",
        "adapter_model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "chat_template.jinja",
        "training_args.bin",
    ]

    for filename in required_artifacts:
        all_passed &= check(
            (ARTIFACT_DIR / filename).is_file(),
            f"Artifact: {filename}",
        )

    print("=" * 40)

    if all_passed:
        print("Overall: PASS")
        return 0

    print("Overall: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())