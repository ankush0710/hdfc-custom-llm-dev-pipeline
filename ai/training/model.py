"""
ai/training/model.py

Loads the base model and attaches a LoRA adapter, ready for a (not-yet-
written) trainer to consume. This module deliberately does three things
and no more:

1. load_base_model()  - load Qwen3-0.6B + tokenizer-free model weights,
                         resolving device/dtype the same way inference does.
2. attach_lora()       - wrap the loaded model with a PEFT LoRA adapter,
                         after verifying the configured target_modules
                         actually exist in this model's architecture.
3. prepare_model()     - orchestrate the two steps above, enable
                         gradient checkpointing, and report parameter
                         counts.

This module does NOT:
- load Member 2's training dataset
- build a Trainer / training loop
- start a real training run
- expose a CLI or API
- modify ai/inference/* (only imports resolve_device as a read-only helper)

ASSUMPTION ABOUT ai/training/lora.py
-------------------------------------
This file assumes ai/training/lora.py exposes:

    def build_lora_config(config: TrainingConfig) -> peft.LoraConfig: ...

If your actual lora.py uses a different function name, update the single
import line below (marked with an ASSUMPTION comment) accordingly -
nothing else in this file needs to change.

Usage
-----
    from ai.training.config import TrainingConfig
    from ai.training.model import prepare_model

    config = TrainingConfig()
    model = prepare_model(config)  # base model loaded, LoRA attached,
                                    # gradient checkpointing enabled

No dataset is loaded and no training step is run by this call.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

import torch
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, PreTrainedModel

from ai.inference.loader import ResolvedDevice, resolve_device  # read-only reuse
from ai.training.config import TrainingConfig
from ai.training.lora import build_lora_config  # ASSUMPTION: see module docstring

logger = logging.getLogger(__name__)


class TrainingModelError(RuntimeError):
    """Base exception for failures in base-model loading or LoRA attachment."""


class BaseModelLoadError(TrainingModelError):
    """Raised when the base model or its weights cannot be loaded safely."""


class LoraAttachmentError(TrainingModelError):
    """Raised when the configured LoRA target_modules do not match the model."""


# ---------------------------------------------------------------------------
# Step 1: base model loading
# ---------------------------------------------------------------------------


def load_base_model(
    config: TrainingConfig, device: str = "auto"
) -> Tuple[PreTrainedModel, ResolvedDevice]:
    """
    Load the base causal LM specified by config.base_model.

    Uses the same device/dtype resolution strategy as the inference engine
    (float16 on CUDA, float32 on CPU) so baseline VRAM behavior already
    measured (~1.1GB peak for Qwen3-0.6B fp16) is a reasonable predictor
    of the memory footprint here, before LoRA/optimizer state is added.

    Parameters
    ----------
    config:
        TrainingConfig; only config.base_model is used at this step.
    device:
        "auto", "cuda", or "cpu". Defaults to "auto".

    Returns
    -------
    (model, resolved_device)

    Raises
    ------
    BaseModelLoadError
        If the model cannot be downloaded/loaded, or does not fit in
        available GPU memory.
    """
    resolved = resolve_device(device)
    logger.info(
        "Loading base model '%s' (device=%s, dtype=%s)...",
        config.base_model,
        resolved.device,
        resolved.dtype,
    )

    try:
        model = AutoModelForCausalLM.from_pretrained(
            config.base_model,
            dtype=resolved.dtype,
            low_cpu_mem_usage=True,
        )
    except OSError as exc:
        raise BaseModelLoadError(
            f"Could not load base model '{config.base_model}'. Verify the "
            "model identifier and that you have internet access or a "
            f"populated local cache. Original error: {exc}"
        ) from exc
    except torch.cuda.OutOfMemoryError as exc:
        raise BaseModelLoadError(
            f"Ran out of GPU memory loading '{config.base_model}' with "
            f"dtype={resolved.dtype}. Try device='cpu', or re-check that "
            "no other process is holding VRAM."
        ) from exc

    try:
        if resolved.device == "cuda":
            model = model.to(resolved.device)
    except torch.cuda.OutOfMemoryError as exc:
        raise BaseModelLoadError(
            f"Ran out of GPU memory moving '{config.base_model}' to CUDA. "
            "This model does not fit in the available VRAM at this "
            "precision. Try device='cpu'."
        ) from exc

    logger.info("Base model loaded on %s.", resolved.device)
    return model, resolved


# ---------------------------------------------------------------------------
# Architecture inspection (used before trusting target_modules)
# ---------------------------------------------------------------------------


def inspect_linear_modules(model: torch.nn.Module) -> Dict[str, int]:
    """
    Return a count of each leaf nn.Linear submodule name found in `model`.

    This is a real runtime inspection of the loaded model's architecture
    (not a hardcoded assumption). For Qwen3-0.6B this should report
    q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj (and
    typically lm_head), each with a count equal to the number of decoder
    layers (except lm_head, which appears once).
    """
    counts: Dict[str, int] = {}
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            leaf_name = name.rsplit(".", 1)[-1]
            counts[leaf_name] = counts.get(leaf_name, 0) + 1
    return counts


def _linear_leaf_names(model: torch.nn.Module) -> Set[str]:
    return set(inspect_linear_modules(model).keys())


def _validate_target_modules(
    model: torch.nn.Module, target_modules: List[str]
) -> None:
    """
    Verify every entry in target_modules matches a real nn.Linear leaf name
    in `model`. Raises LoraAttachmentError with the actual available names
    if any target is missing, instead of letting PEFT silently attach
    zero adapters (a common, hard-to-notice failure mode).
    """
    available = _linear_leaf_names(model)
    missing = [t for t in target_modules if t not in available]
    if missing:
        raise LoraAttachmentError(
            f"LoRA target_modules {missing} were not found as nn.Linear "
            f"layers in the loaded model. Linear layers actually present: "
            f"{sorted(available)}. Update ai/training/lora.py's "
            "target_modules to match the real architecture."
        )


# ---------------------------------------------------------------------------
# Step 2: LoRA attachment
# ---------------------------------------------------------------------------


def attach_lora(model: PreTrainedModel, config: TrainingConfig) -> PeftModel:
    """
    Attach a LoRA adapter (built from config via ai.training.lora) to an
    already-loaded base model.

    Raises
    ------
    LoraAttachmentError
        If the configured target_modules do not exist in the model, or if
        PEFT fails to attach the adapter for any other reason.
    """
    lora_config: LoraConfig = build_lora_config(config)

    _validate_target_modules(model, list(lora_config.target_modules))

    try:
        peft_model = get_peft_model(model, lora_config)
    except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
        raise LoraAttachmentError(
            f"Failed to attach LoRA adapter to '{config.base_model}': {exc}"
        ) from exc

    logger.info(
        "LoRA attached: r=%d, alpha=%d, dropout=%.2f, target_modules=%s",
        lora_config.r,
        lora_config.lora_alpha,
        lora_config.lora_dropout,
        list(lora_config.target_modules),
    )
    return peft_model


# ---------------------------------------------------------------------------
# Parameter accounting
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterSummary:
    """Summary of total vs. trainable parameters for a model."""

    total_parameters: int
    trainable_parameters: int
    trainable_percentage: float


def count_parameters(model: torch.nn.Module) -> ParameterSummary:
    """
    Count total and trainable parameters in `model`.

    For a correctly-configured LoRA attachment on Qwen3-0.6B, expect
    trainable_percentage in roughly the 0.1-0.3% range. A much larger
    percentage (e.g. tens of percent) is a strong signal that the base
    model was not actually frozen and should be treated as a failure.
    """
    total = 0
    trainable = 0
    for param in model.parameters():
        n = param.numel()
        total += n
        if param.requires_grad:
            trainable += n

    percentage = (trainable / total * 100.0) if total > 0 else 0.0
    return ParameterSummary(
        total_parameters=total,
        trainable_parameters=trainable,
        trainable_percentage=round(percentage, 4),
    )


# ---------------------------------------------------------------------------
# Step 3: orchestration
# ---------------------------------------------------------------------------


def prepare_model(
    config: TrainingConfig,
    device: str = "auto",
    enable_gradient_checkpointing: bool = True,
) -> PeftModel:
    """
    Load the base model, attach LoRA, and prepare it for training.

    This function does NOT load a dataset, build a Trainer, or start
    training. It returns a PEFT-wrapped model with the base weights
    frozen and only LoRA adapter weights trainable.

    Parameters
    ----------
    config:
        TrainingConfig describing the base model and LoRA hyperparameters.
    device:
        "auto", "cuda", or "cpu". Defaults to "auto".
    enable_gradient_checkpointing:
        If True (default), enables gradient checkpointing and
        `enable_input_require_grads()` (required for gradient
        checkpointing to work correctly with a frozen base model +
        trainable LoRA adapters) to reduce activation memory - useful on
        a 4GB GPU.

    Returns
    -------
    PeftModel
        Ready for a trainer to consume. Not yet in training.

    Raises
    ------
    BaseModelLoadError, LoraAttachmentError
    """
    torch.manual_seed(config.seed)

    model, resolved = load_base_model(config, device=device)

    linear_counts = inspect_linear_modules(model)
    logger.info("Discovered linear submodules: %s", linear_counts)

    peft_model = attach_lora(model, config)

    if enable_gradient_checkpointing:
        # use_cache and gradient checkpointing are mutually incompatible:
        # caching stores past key/values to skip recomputation, which
        # directly conflicts with checkpointing's recompute-on-backward
        # strategy. This must be set before enabling checkpointing.
        peft_model.config.use_cache = False
        peft_model.gradient_checkpointing_enable()
        peft_model.enable_input_require_grads()
        logger.info("Gradient checkpointing enabled (use_cache=False).")

    summary = count_parameters(peft_model)
    logger.info(
        "Parameter summary: total=%s trainable=%s (%.4f%%)",
        f"{summary.total_parameters:,}",
        f"{summary.trainable_parameters:,}",
        summary.trainable_percentage,
    )

    if summary.trainable_parameters == 0:
        raise LoraAttachmentError(
            "LoRA attachment produced zero trainable parameters. The base "
            "model is not actually adaptable in this state - check "
            "target_modules in ai/training/lora.py."
        )

    return peft_model