import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Repository roots
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
AI_ROOT = PROJECT_ROOT / "ai"

# Standard artifact search locations
ARTIFACT_SEARCH_DIRS = [
    PROJECT_ROOT / "ai" / "artifacts",
    PROJECT_ROOT / "backend" / "ai" / "artifacts",
    PROJECT_ROOT / "artifacts",
]

# Required file signatures
LORA_ADAPTER_REQUIRED = ["adapter_config.json", "adapter_model.safetensors"]
FULL_MODEL_REQUIRED = ["config.json"]


def resolve_artifact_path(path_input: Union[str, Path, None]) -> Optional[Path]:
    """
    Robustly resolves an artifact or adapter path across the repository.
    Handles relative paths, absolute Windows/POSIX paths, and cross-root
    variations (backend/ai/artifacts vs ai/artifacts).
    """
    if not path_input:
        return None

    cleaned_str = str(path_input).strip().strip('"').strip("'")
    if not cleaned_str:
        return None

    candidate = Path(cleaned_str)

    # 1. Direct path check (if absolute or valid relative to current working dir)
    if candidate.is_dir() and _has_model_signature(candidate):
        return candidate.resolve()

    # 2. Check relative to PROJECT_ROOT, BACKEND_ROOT, and AI_ROOT
    for root in [PROJECT_ROOT, BACKEND_ROOT, AI_ROOT]:
        p = (root / candidate).resolve()
        if p.is_dir() and _has_model_signature(p):
            return p

    # 3. Check stripped prefix variations (e.g. if path starts with "ai/" or "backend/")
    norm_path = cleaned_str.replace("\\", "/").lstrip("/")
    prefixes_to_strip = ["backend/ai/artifacts/", "backend/ai/", "backend/", "ai/artifacts/", "ai/", "artifacts/"]
    
    sub_path = norm_path
    for pfx in prefixes_to_strip:
        if norm_path.startswith(pfx):
            sub_path = norm_path[len(pfx):]
            break

    for search_dir in ARTIFACT_SEARCH_DIRS:
        # Direct join with search_dir
        c1 = (search_dir / sub_path).resolve()
        if c1.is_dir() and _has_model_signature(c1):
            return c1
        # Try joining norm_path
        c2 = (search_dir / norm_path).resolve()
        if c2.is_dir() and _has_model_signature(c2):
            return c2

    # 4. If directory exists anywhere even without standard weights yet
    if candidate.is_dir():
        return candidate.resolve()
    for root in [PROJECT_ROOT, BACKEND_ROOT, AI_ROOT]:
        p = (root / candidate).resolve()
        if p.is_dir():
            return p

    return None


def _has_model_signature(dir_path: Path) -> bool:
    """Checks if a directory contains either LoRA adapter files or full model files."""
    if not dir_path.is_dir():
        return False
    # Check for adapter config or full model config
    has_adapter = (dir_path / "adapter_config.json").is_file()
    has_full = (dir_path / "config.json").is_file()
    return has_adapter or has_full


def validate_artifact_directory(path_input: Union[str, Path, None]) -> Dict[str, Any]:
    """
    Validates a model or adapter directory and determines its type.
    
    Returns
    -------
    dict with:
      - is_valid (bool)
      - model_type ("lora_adapter" | "full_model" | "invalid")
      - resolved_path (Optional[Path])
      - base_model (Optional[str])
      - missing_files (List[str])
      - error_message (Optional[str])
    """
    if not path_input:
        return {
            "is_valid": False,
            "model_type": "invalid",
            "resolved_path": None,
            "base_model": None,
            "missing_files": [],
            "error_message": "Artifact path is empty or not provided.",
        }

    resolved = resolve_artifact_path(path_input)
    if not resolved or not resolved.is_dir():
        return {
            "is_valid": False,
            "model_type": "invalid",
            "resolved_path": None,
            "base_model": None,
            "missing_files": [],
            "error_message": f"Model artifact directory not found on disk: '{path_input}'",
        }

    # Check for LoRA Adapter
    adapter_cfg_file = resolved / "adapter_config.json"
    if adapter_cfg_file.is_file():
        # Check adapter weights
        has_weights = (
            (resolved / "adapter_model.safetensors").is_file()
            or (resolved / "adapter_model.bin").is_file()
        )
        if not has_weights:
            return {
                "is_valid": False,
                "model_type": "lora_adapter",
                "resolved_path": resolved,
                "base_model": None,
                "missing_files": ["adapter_model.safetensors"],
                "error_message": f"Adapter configuration exists in '{resolved}', but adapter_model.safetensors weights are missing.",
            }

        base_model_name = None
        try:
            with adapter_cfg_file.open("r", encoding="utf-8") as f:
                cfg_data = json.load(f)
                base_model_name = cfg_data.get("base_model_name_or_path")
        except Exception as err:
            logger.warning("Failed to parse adapter_config.json: %s", err)

        return {
            "is_valid": True,
            "model_type": "lora_adapter",
            "resolved_path": resolved,
            "base_model": base_model_name,
            "missing_files": [],
            "error_message": None,
        }

    # Check for Full Pretrained Model
    model_cfg_file = resolved / "config.json"
    if model_cfg_file.is_file():
        has_weights = (
            (resolved / "model.safetensors").is_file()
            or (resolved / "pytorch_model.bin").is_file()
            or any(resolved.glob("*.safetensors"))
            or any(resolved.glob("*.bin"))
        )
        if not has_weights:
            return {
                "is_valid": False,
                "model_type": "full_model",
                "resolved_path": resolved,
                "base_model": None,
                "missing_files": ["model.safetensors"],
                "error_message": f"Model config exists in '{resolved}', but model weights (*.safetensors) are missing.",
            }

        return {
            "is_valid": True,
            "model_type": "full_model",
            "resolved_path": resolved,
            "base_model": None,
            "missing_files": [],
            "error_message": None,
        }

    return {
        "is_valid": False,
        "model_type": "invalid",
        "resolved_path": resolved,
        "base_model": None,
        "missing_files": ["adapter_config.json or config.json"],
        "error_message": (
            f"Directory '{resolved}' exists, but does not contain valid model files "
            f"(neither adapter_config.json for LoRA adapters nor config.json for full models)."
        ),
    }
