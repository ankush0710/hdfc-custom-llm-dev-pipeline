"""
ai/inference/service.py

Application-facing inference service layer for the HDFC Custom LLM project.

Provides ONE common interface (`run_model`) for Member 3's backend/frontend
integration, wrapping the real existing modules:

    ai/inference/loader.py     -> ModelLoader(model_name, device=...).load()
    ai/inference/generator.py  -> generate(tokenizer, model, prompt, model_name,
                                            device, generation_config)
                                   GenerationConfig(...)
    ai/inference/finetuned.py  -> load_finetuned_model(base_model, adapter_path,
                                                         device)
                                   generate_finetuned(bundle, question, context,
                                                       generation_config)
                                   FinetunedModelBundle

None of loader.py, generator.py, finetuned.py, training code, or datasets are
modified by this file.

Registry note
-------------
ai/config/model/model_registry.yaml currently only provides `name` and
`enabled` per model. It does NOT contain `fine_tuned` / `adapter_path`.
Per instructions, the HDFC fine-tuning mapping is therefore defined
explicitly and centrally in this file (`_MODEL_MAP` below), not inferred
from the registry. The registry is still consulted for `enabled` status.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import yaml

from ai.inference.loader import ModelLoader
from ai.inference.generator import generate as generate_baseline, GenerationConfig
from ai.inference.finetuned import (
    load_finetuned_model,
    generate_finetuned,
    FinetunedModelBundle,
)

from pathlib import Path


# --------------------------------------------------------------------------
# Project paths
# --------------------------------------------------------------------------

# service.py:
# <project-root>/ai/inference/service.py
#
# parents[0] -> ai/inference
# parents[1] -> ai
# parents[2] -> project-root

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AI_ROOT = PROJECT_ROOT / "ai"

REGISTRY_YAML_PATH = (
    AI_ROOT
    / "config"
    / "model_registry.yaml"
)

FULL_TRAINING_ADAPTER_PATH = (
    AI_ROOT
    / "artifacts"
    / "full_training"
)

TASK_INTENT_CLASSIFICATION = "intent_classification"
TASK_SFT_GROUNDED_GENERATION = "sft_grounded_generation"
TASK_CUSTOMER_FAQ_QA = "customer_faq_qa"
TASK_DOMAIN_CONCEPT_QA = "domain_concept_qa"

SUPPORTED_TASKS = {
    TASK_INTENT_CLASSIFICATION,
    TASK_SFT_GROUNDED_GENERATION,
    TASK_CUSTOMER_FAQ_QA,
    TASK_DOMAIN_CONCEPT_QA,
}

# ==========================================================================
# Central HDFC fine-tuning map (NOT sourced from model_registry.yaml, since
# the registry does not carry fine_tuned / adapter_path fields today).
# Only qwen3_0_6b has an HDFC LoRA adapter.
# ==========================================================================
_MODEL_MAP: Dict[str, Dict[str, Any]] = {
    "qwen3_0_6b": {
        "base_model": "Qwen/Qwen3-0.6B",
        "fine_tuned": True,
        "adapter_path": str(FULL_TRAINING_ADAPTER_PATH),
    },

    "qwen2_5_1_5b_instruct": {
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "fine_tuned": False,
    },

    "smollm2_1_7b_instruct": {
        "base_model": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
        "fine_tuned": False,
    },
}

# ==========================================================================
# Errors
# ==========================================================================
class InferenceServiceError(Exception):
    """Base class for all service-layer errors."""


class UnknownModelError(InferenceServiceError):
    def __init__(self, model_id: str, available: List[str]) -> None:
        super().__init__(
            f"Unknown model_id '{model_id}'. Available model IDs: {available}"
        )
        self.model_id = model_id


class ModelDisabledError(InferenceServiceError):
    def __init__(self, model_id: str) -> None:
        super().__init__(f"Model '{model_id}' is disabled in the registry.")
        self.model_id = model_id


class UnsupportedTaskError(InferenceServiceError):
    def __init__(self, task_type: str, available: List[str]) -> None:
        super().__init__(
            f"Unsupported task_type '{task_type}'. Supported task types: {available}"
        )
        self.task_type = task_type


class ModelLoadError(InferenceServiceError):
    def __init__(self, model_id: str, detail: str) -> None:
        super().__init__(f"Failed to load model '{model_id}': {detail}")
        self.model_id = model_id


class MissingAdapterError(InferenceServiceError):
    def __init__(self, model_id: str, adapter_path: Optional[str]) -> None:
        super().__init__(
            f"HDFC adapter for model '{model_id}' not found at "
            f"'{adapter_path}'. Fine-tuned models require a valid adapter."
        )
        self.model_id = model_id
        self.adapter_path = adapter_path


class GenerationError(InferenceServiceError):
    def __init__(self, model_id: str, detail: str) -> None:
        super().__init__(f"Generation failed for model '{model_id}': {detail}")
        self.model_id = model_id


class CudaOutOfMemoryError(InferenceServiceError):
    def __init__(self, model_id: str, phase: str) -> None:
        super().__init__(
            f"CUDA out of memory while {phase} model '{model_id}'. "
            f"Call unload_model() to free GPU memory before loading another "
            f"model, or reduce max_new_tokens."
        )
        self.model_id = model_id


# ==========================================================================
# Registry access (used only for `enabled` status)
# ==========================================================================
def _normalize_registry(raw: Any) -> Dict[str, Dict[str, Any]]:
    """Normalize registry data into an id -> config dict.

    Supports the actual format (a list of entries, each with an 'id' field,
    e.g. under a top-level 'models' key) as well as a plain dict mapping
    (id -> config), defensively.
    """
    if isinstance(raw, dict) and "models" in raw:
        raw = raw["models"]

    if isinstance(raw, list):
        normalized: Dict[str, Dict[str, Any]] = {}
        for entry in raw:
            if isinstance(entry, dict) and "id" in entry:
                normalized[entry["id"]] = entry
        return normalized

    if isinstance(raw, dict):
        return raw

    return {}


def _load_registry_from_yaml() -> Dict[str, Dict[str, Any]]:
    with open(REGISTRY_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return _normalize_registry(data)


def _get_registry() -> Dict[str, Dict[str, Any]]:
    try:
        from ai.models.registry import load_model_registry

        return _normalize_registry(load_model_registry())
    except Exception:
        return _load_registry_from_yaml()


def _is_enabled(model_id: str) -> bool:
    try:
        registry = _get_registry()
        cfg = registry.get(model_id)
        if cfg is None:
            return True  # not in registry yet -> don't block on missing entry
        return bool(cfg.get("enabled", True))
    except Exception:
        return True  # registry unreadable -> fail open on enabled status only


def _get_model_map_entry(model_id: str) -> Dict[str, Any]:
    if model_id not in _MODEL_MAP:
        raise UnknownModelError(model_id, sorted(_MODEL_MAP.keys()))
    return _MODEL_MAP[model_id]


# ==========================================================================
# Single active-model cache (4 GB VRAM constraint: only one model at a time)
# ==========================================================================
@dataclass
class _ActiveModel:
    model_id: str
    fine_tuned: bool
    # Populated for base (non-fine-tuned) models:
    tokenizer: Optional[Any] = None
    model: Optional[Any] = None
    resolved_device: Optional[Any] = None
    # Populated for the fine-tuned model:
    bundle: Optional[FinetunedModelBundle] = None


_active: Optional[_ActiveModel] = None


def _device_str(resolved_device: Any) -> str:
    """Best-effort conversion of loader.py's ResolvedDevice into a string,
    since generate()'s `device` parameter is typed as str."""
    for attr in ("device", "device_str", "name"):
        val = getattr(resolved_device, attr, None)
        if isinstance(val, str):
            return val
    return str(resolved_device)


def _load_base(model_id: str, entry: Dict[str, Any]) -> _ActiveModel:
    loader = ModelLoader(model_name=entry["base_model"], device="auto")
    tokenizer, model, resolved = loader.load()
    return _ActiveModel(
        model_id=model_id,
        fine_tuned=False,
        tokenizer=tokenizer,
        model=model,
        resolved_device=resolved,
    )


def _load_finetuned(
    model_id: str,
    entry: Dict[str, Any]
) -> _ActiveModel:

    adapter_path = Path(entry["adapter_path"])

    # Validate adapter directory
    if not adapter_path.is_dir():
        raise MissingAdapterError(
            model_id,
            str(adapter_path)
        )

    # Validate required PEFT files
    required_files = [
        "adapter_config.json",
        "adapter_model.safetensors",
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (adapter_path / filename).is_file()
    ]

    if missing_files:
        raise MissingAdapterError(
            model_id,
            (
                f"{adapter_path} "
                f"(missing: {', '.join(missing_files)})"
            )
        )

    bundle = load_finetuned_model(
        base_model=entry["base_model"],
        adapter_path=adapter_path,
        device="auto",
    )

    return _ActiveModel(
        model_id=model_id,
        fine_tuned=True,
        bundle=bundle,
    )


def _get_or_load(model_id: str, entry: Dict[str, Any]) -> _ActiveModel:
    global _active

    if _active is not None and _active.model_id == model_id:
        return _active

    if _active is not None and _active.model_id != model_id:
        unload_model()

    try:
        if entry["fine_tuned"]:
            loaded = _load_finetuned(model_id, entry)
        else:
            loaded = _load_base(model_id, entry)
    except MissingAdapterError:
        raise
    except torch.cuda.OutOfMemoryError as exc:  # type: ignore[attr-defined]
        raise CudaOutOfMemoryError(model_id, "loading") from exc
    except Exception as exc:
        raise ModelLoadError(model_id, str(exc)) from exc

    _active = loaded
    return _active


def unload_model() -> Dict[str, Any]:
    """Explicitly unload the currently loaded model and free GPU memory.

    Safe to call when nothing is loaded. Also called automatically inside
    run_model() when switching to a different model_id, since only one
    model may be resident at a time on the 4 GB GPU.
    """
    global _active
    if _active is None:
        return {"unloaded": None, "message": "No model currently loaded."}

    unloaded_id = _active.model_id
    model_ref = _active.model
    tokenizer_ref = _active.tokenizer
    bundle_ref = _active.bundle
    _active = None

    del model_ref
    del tokenizer_ref
    del bundle_ref
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "unloaded": unloaded_id,
        "message": f"Model '{unloaded_id}' unloaded and GPU memory released.",
    }


# ==========================================================================
# Task-aware prompt formatting
# ==========================================================================
def _build_task_input(
    task_type: str, question: str, context: Optional[str]
) -> Tuple[str, Optional[str]]:
    """Build (question, context) to hand to the generation backend.

    No system prompt is constructed here. For qwen3_0_6b, generate_finetuned()
    owns the HDFC system prompt and the Qwen chat template — untouched.
    """
    if task_type == TASK_INTENT_CLASSIFICATION:
        formatted_question = (
            "Classify the intent for this customer query:\n\n" f"{question.strip()}"
        )
        return formatted_question, context

    if task_type in (
        TASK_SFT_GROUNDED_GENERATION,
        TASK_CUSTOMER_FAQ_QA,
        TASK_DOMAIN_CONCEPT_QA,
    ):
        return question.strip(), context

    raise UnsupportedTaskError(task_type, sorted(SUPPORTED_TASKS))


def _parse_response_if_json(response_text: str) -> Union[Dict[str, Any], str]:
    """Return response_text parsed into a dict if (and only if) it is a
    valid JSON object; otherwise return response_text unchanged.

    This is pure post-processing of an already-generated string — it does
    not affect prompting, generation, or model behavior. Only strict
    json.loads() is used (no regex/brace scraping), and only a JSON
    *object* (dict) is converted — JSON arrays, numbers, strings, booleans,
    and null are all left as the original string, since the frontend only
    benefits from structured objects like intent/citation payloads.
    """
    candidate = response_text.strip()
    if not candidate:
        return response_text
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return response_text
    if isinstance(parsed, dict):
        return parsed
    return response_text



def _baseline_prompt(formatted_question: str, context: Optional[str]) -> str:
    """Plain-text fallback prompt, used when a tokenizer has no chat
    template. No HDFC system prompt is applied — these models are not
    HDFC fine-tuned."""
    if context:
        return f"Context:\n{context.strip()}\n\n{formatted_question}"
    return formatted_question


def _build_base_model_prompt(
    tokenizer: Any, formatted_question: str, context: Optional[str]
) -> str:
    """Build the prompt string for a non-fine-tuned base/instruct model.

    Many instruct/chat checkpoints (e.g. SmolLM2-1.7B-Instruct) are trained
    to only respond sensibly to input wrapped in their chat template's
    special tokens. Feeding such a model a raw plain-text prompt (no
    template) can produce degenerate output, including an empty string,
    even though loading and the forward pass succeed without error.

    This uses tokenizer.apply_chat_template() when the tokenizer exposes a
    chat_template, generically for any instruct/chat model — no
    model-specific token IDs or architecture assumptions. When no chat
    template is available, it falls back to the plain-text prompt path.

    No HDFC system prompt is applied here; the system message is a generic
    assistant framing only, since these models are not HDFC fine-tuned.
    """
    chat_template = getattr(tokenizer, "chat_template", None)
    if chat_template:
        user_content = (
            f"Context: {context.strip()}\n\n{formatted_question}"
            if context
            else formatted_question
        )
        messages = [
            {"role": "system", "content": "You are a helpful banking assistant."},
            {"role": "user", "content": user_content},
        ]
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:
            pass  # fall through to the plain-text prompt below

    return _baseline_prompt(formatted_question, context)


# ==========================================================================
# Public API
# ==========================================================================
def get_available_models() -> List[Dict[str, Any]]:
    """Return the central model map + runtime status for every model.

    Each entry contains: id, name, fine_tuned, adapter_available, enabled,
    currently_loaded.
    """
    results: List[Dict[str, Any]] = []
    for model_id, entry in _MODEL_MAP.items():
        adapter_path = entry.get("adapter_path")
        adapter_available = bool(adapter_path) and os.path.isdir(adapter_path)
        results.append(
            {
                "id": model_id,
                "name": entry["base_model"],
                "fine_tuned": bool(entry["fine_tuned"]),
                "adapter_available": adapter_available,
                "enabled": _is_enabled(model_id),
                "currently_loaded": _active is not None
                and _active.model_id == model_id,
            }
        )
    return results


def run_model(
    model_id: str,
    task_type: str,
    question: str,
    context: Optional[str] = None,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
    top_p: float = 0.9,
    do_sample: bool = False,
    seed: int = 42,
    adapter_path_override: Optional[str] = None,
    base_model_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Run inference for a single (model, task, question) request.

    Returns a structured result dict:
        model_id, model_name, fine_tuned, task_type, question, context,
        response, raw_response, latency_seconds, device

    `response` is the parsed Python dict when the model's raw output is a
    valid JSON object (e.g. intent classification, structured grounded
    generation), or the original string otherwise. `raw_response` always
    holds the original, unparsed model output string.

    Raises:
        UnknownModelError, ModelDisabledError, UnsupportedTaskError,
        ModelLoadError, MissingAdapterError, GenerationError,
        CudaOutOfMemoryError
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("`question` must be a non-empty string.")

    if task_type not in SUPPORTED_TASKS:
        raise UnsupportedTaskError(task_type, sorted(SUPPORTED_TASKS))

    # ------------------------------------------------------------------
    # Resolve model entry — prefer _MODEL_MAP, apply DB-sourced overrides
    # ------------------------------------------------------------------
    if model_id in _MODEL_MAP:
        entry = dict(_MODEL_MAP[model_id])          # mutable copy
        if base_model_override:
            entry["base_model"] = base_model_override
        if adapter_path_override:
            entry["adapter_path"] = adapter_path_override
            entry["fine_tuned"] = True
    elif base_model_override:
        # Model not yet in _MODEL_MAP — build from DB-sourced fields
        entry = {
            "base_model": base_model_override,
            "fine_tuned": bool(adapter_path_override),
        }
        if adapter_path_override:
            entry["adapter_path"] = adapter_path_override
    else:
        raise UnknownModelError(model_id, sorted(_MODEL_MAP.keys()))

    if not _is_enabled(model_id):
        raise ModelDisabledError(model_id)

    fine_tuned = bool(entry["fine_tuned"])
    model_name = entry["base_model"]

    formatted_question, formatted_context = _build_task_input(
        task_type, question, context
    )

    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=do_sample,
        seed=seed,
    )

    loaded = _get_or_load(model_id, entry)

    try:
        if fine_tuned:
            ft_result = generate_finetuned(
                loaded.bundle,
                question=formatted_question,
                context=formatted_context,
                generation_config=gen_config,
            )
            response_text = ft_result.get("response")
            latency = ft_result.get("latency_seconds")
            device = ft_result.get("device")
            if response_text is None:
                raise GenerationError(
                    model_id, "generate_finetuned() returned no 'response' field."
                )
        else:
            prompt = _build_base_model_prompt(
                loaded.tokenizer, formatted_question, formatted_context
            )
            device = _device_str(loaded.resolved_device)
            start = time.time()
            base_result = generate_baseline(
                tokenizer=loaded.tokenizer,
                model=loaded.model,
                prompt=prompt,
                model_name=model_name,
                device=device,
                generation_config=gen_config,
            )
            latency = time.time() - start
            response_text = (
                base_result.get("response")
                if isinstance(base_result, dict)
                else None
            )
            if response_text is None:
                raise GenerationError(
                    model_id,
                    "generate() returned no usable 'response' field in its result dict.",
                )
    except torch.cuda.OutOfMemoryError as exc:  # type: ignore[attr-defined]
        raise CudaOutOfMemoryError(model_id, "generating with") from exc
    except InferenceServiceError:
        raise
    except Exception as exc:
        raise GenerationError(model_id, str(exc)) from exc

    return {
        "model_id": model_id,
        "model_name": model_name,
        "fine_tuned": fine_tuned,
        "task_type": task_type,
        "question": question,
        "context": context,
        "response": _parse_response_if_json(response_text),
        "raw_response": response_text,
        "latency_seconds": round(float(latency), 3) if latency is not None else None,
        "device": device,
    }


# ==========================================================================
# CLI smoke test
# ==========================================================================
def _cli() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m ai.inference.service",
        description="HDFC Custom LLM inference service — smoke test CLI",
    )
    parser.add_argument("--model", help="Model ID, e.g. qwen3_0_6b")
    parser.add_argument("--task", choices=sorted(SUPPORTED_TASKS), help="Task type")
    parser.add_argument("--question", help="Customer/user query")
    parser.add_argument("--context", default=None, help="Optional authoritative context")
    parser.add_argument("--max-new-tokens", type=int, default=256, dest="max_new_tokens")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--unload", action="store_true")
    args = parser.parse_args()

    if args.list_models:
        print(json.dumps(get_available_models(), indent=2))
        return

    if args.unload:
        print(json.dumps(unload_model(), indent=2))
        return

    if not (args.model and args.task and args.question):
        parser.error(
            "--model, --task, and --question are required "
            "(unless using --list-models or --unload)"
        )

    try:
        result = run_model(
            model_id=args.model,
            task_type=args.task,
            question=args.question,
            context=args.context,
            max_new_tokens=args.max_new_tokens,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except InferenceServiceError as exc:
        print(f"[service error] {exc}")
        raise SystemExit(1)
    except Exception:
        print("[unexpected error]")
        traceback.print_exc()
        raise SystemExit(1)

# ================================================================================================ #
# temparory debugger for path
# ================================================================================================ #
def get_ai_paths() -> Dict[str, Any]:
    adapter_path = Path(
        _MODEL_MAP["qwen3_0_6b"]["adapter_path"]
    )

    return {
        "project_root": str(PROJECT_ROOT),
        "ai_root": str(AI_ROOT),
        "registry_path": str(REGISTRY_YAML_PATH),
        "registry_exists": REGISTRY_YAML_PATH.is_file(),
        "adapter_path": str(adapter_path),
        "adapter_exists": adapter_path.is_dir(),
        "adapter_config_exists": (
            adapter_path / "adapter_config.json"
        ).is_file(),
        "adapter_model_exists": (
            adapter_path / "adapter_model.safetensors"
        ).is_file(),
    }

if __name__ == "__main__":
    _cli()