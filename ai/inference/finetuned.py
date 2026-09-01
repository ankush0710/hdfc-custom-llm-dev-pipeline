"""
ai/inference/finetuned.py

Production inference path for the HDFC fine-tuned Qwen3-0.6B LoRA adapter.

This module is deliberately separate from ai/inference/baseline.py (see
the accompanying explanation): it reuses ai.inference.loader.resolve_device
and ai.inference.generator.generate() completely unchanged, and adds only
what's genuinely new for a fine-tuned, adapter-based model - attaching the
LoRA adapter via PEFT, and building the chat-templated conversation the
adapter was actually trained on.

Responsibilities
-----------------
- Load the base model (Qwen/Qwen3-0.6B by default).
- Attach the trained LoRA adapter via PeftModel.from_pretrained() - never
  merged into the base weights (the returned model stays a PeftModel).
- Load the tokenizer from the adapter directory (which contains the exact
  tokenizer/chat_template.jinja used at training time), falling back to
  the base model's tokenizer only if that's unavailable.
- Build a system + user conversation and render it with
  add_generation_prompt=True, enable_thinking=False - matching how the
  adapter was trained (enable_thinking=False was also used to build the
  training text; see ai/training/train.py).
- Generate a response via the existing, unmodified generate() from
  ai.inference.generator, decoding only the newly generated tokens.
- Return a structured result and provide a CLI.

This module does NOT:
- modify ai/inference/loader.py, generator.py, or baseline.py
- modify any training code or the dataset
- merge the LoRA adapter into the base model
- force adapter support into ModelLoader

Usage
-----
    from ai.inference.finetuned import load_finetuned_model, generate_finetuned

    bundle = load_finetuned_model()
    result = generate_finetuned(bundle, "How do I report a suspicious KYC SMS?")
    print(result["response"])

CLI
---
    python -m ai.inference.finetuned --prompt "How do I report a suspicious KYC SMS?"
    python -m ai.inference.finetuned --prompt "..." --output ai/artifacts/finetuned_run1.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedTokenizerBase

from ai.inference.generator import GenerationConfig, generate
from ai.inference.loader import ResolvedDevice, resolve_device
from ai.utils.path_utils import resolve_artifact_path, validate_artifact_directory

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_MODEL = "Qwen/Qwen3-0.6B"
DEFAULT_ADAPTER_PATH = PROJECT_ROOT / "ai" / "artifacts" / "full_training"
DEFAULT_SYSTEM_PROMPT = "You are a helpful and accurate HDFC Bank assistant."
REQUIRED_ADAPTER_FILES = ("adapter_config.json", "adapter_model.safetensors")


class FinetunedInferenceError(RuntimeError):
    """Base exception for the fine-tuned inference path."""


class AdapterNotFoundError(FinetunedInferenceError):
    """Raised when the adapter directory or its required files are missing."""


class FinetunedLoadError(FinetunedInferenceError):
    """Raised when the base model, tokenizer, or adapter fail to load."""


class FinetunedGenerationError(FinetunedInferenceError):
    """Raised when generation itself fails (e.g. GPU OOM during model.generate())."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


@dataclass
class FinetunedModelBundle:
    """Everything needed to run fine-tuned inference: model, tokenizer, and
    the resolved device/paths used to load them."""

    model: PeftModel
    tokenizer: PreTrainedTokenizerBase
    base_model_name: str
    adapter_path: Path
    resolved_device: ResolvedDevice


def _validate_adapter_path(adapter_path: Path) -> Path:
    """
    Verify the adapter directory and its required PEFT files exist,
    failing with a clear, specific error rather than an obscure
    downstream exception from PeftModel.from_pretrained().
    """
    resolved = resolve_artifact_path(adapter_path)
    if not resolved or not resolved.is_dir():
        raise AdapterNotFoundError(
            f"Adapter directory not found: {adapter_path}. This should be "
            "the output directory of the training pipeline (containing "
            "adapter_config.json and adapter_model.safetensors)."
        )

    missing = [
        name for name in REQUIRED_ADAPTER_FILES if not (resolved / name).exists()
    ]
    if missing:
        raise AdapterNotFoundError(
            f"Adapter directory '{resolved}' is missing required file(s): "
            f"{missing}. A valid PEFT LoRA adapter directory must contain "
            "both adapter_config.json and adapter_model.safetensors."
        )

    return resolved


def load_finetuned_model(
    base_model: str = DEFAULT_BASE_MODEL,
    adapter_path: Union[str, Path] = DEFAULT_ADAPTER_PATH,
    device: str = "auto",
    trust_remote_code: bool = False,
) -> FinetunedModelBundle:
    """
    Load the base model, attach the trained LoRA adapter, and load the
    matching tokenizer.

    The adapter is attached via PeftModel.from_pretrained() and is NEVER
    merged into the base weights - the returned model is a PeftModel
    wrapping the frozen base + adapter deltas, exactly matching how it
    was trained.

    Parameters
    ----------
    base_model:
        Hugging Face identifier of the base model.
    adapter_path:
        Path to the trained LoRA adapter directory.
    device:
        "auto", "cuda", or "cpu".
    trust_remote_code:
        Passed through to from_pretrained calls. Defaults to False.

    Raises
    ------
    AdapterNotFoundError
        If the adapter directory or its required files are missing.
    FinetunedLoadError
        If the base model, adapter, or tokenizer fail to load (including
        GPU out-of-memory, translated into a clear message).
    """
    adapter_path = _validate_adapter_path(Path(adapter_path))

    # Read base model from adapter_config.json if not explicitly customized
    adapter_cfg = adapter_path / "adapter_config.json"
    if adapter_cfg.is_file() and (not base_model or base_model == DEFAULT_BASE_MODEL):
        try:
            with adapter_cfg.open("r", encoding="utf-8") as f:
                cfg_dict = json.load(f)
                if cfg_dict.get("base_model_name_or_path"):
                    base_model = cfg_dict["base_model_name_or_path"]
        except Exception:
            pass

    resolved = resolve_device(device)
    logger.info(
        "Loading base model '%s' (device=%s, dtype=%s)...",
        base_model,
        resolved.device,
        resolved.dtype,
    )

    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            dtype=resolved.dtype,
            low_cpu_mem_usage=True,
            trust_remote_code=trust_remote_code,
        )
    except OSError as exc:
        raise FinetunedLoadError(
            f"Could not load base model '{base_model}'. Verify the model "
            f"identifier and network/cache access. Original error: {exc}"
        ) from exc
    except torch.cuda.OutOfMemoryError as exc:
        raise FinetunedLoadError(
            f"Ran out of GPU memory loading base model '{base_model}' with "
            f"dtype={resolved.dtype}. Try device='cpu'."
        ) from exc

    try:
        if resolved.device == "cuda":
            model = model.to(resolved.device)
    except torch.cuda.OutOfMemoryError as exc:
        raise FinetunedLoadError(
            f"Ran out of GPU memory moving base model '{base_model}' to "
            "CUDA. Try device='cpu'."
        ) from exc

    logger.info("Attaching LoRA adapter from %s...", adapter_path)
    try:
        model = PeftModel.from_pretrained(model, str(adapter_path))
    except torch.cuda.OutOfMemoryError as exc:
        raise FinetunedLoadError(
            f"Ran out of GPU memory attaching the LoRA adapter from "
            f"{adapter_path}. Try device='cpu'."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
        raise FinetunedLoadError(
            f"Failed to attach LoRA adapter from {adapter_path}: {exc}"
        ) from exc

    model.eval()

    # Prefer the tokenizer saved alongside the adapter - it includes the
    # exact chat_template.jinja used at training time. Fall back to the
    # base model's tokenizer only if that's unavailable.
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            str(adapter_path), trust_remote_code=trust_remote_code
        )
    except OSError:
        logger.warning(
            "No tokenizer found in adapter directory %s; falling back to "
            "the base model tokenizer '%s'.",
            adapter_path,
            base_model,
        )
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                base_model, trust_remote_code=trust_remote_code
            )
        except OSError as exc:
            raise FinetunedLoadError(
                f"Could not load a tokenizer from either {adapter_path} or "
                f"'{base_model}'. Original error: {exc}"
            ) from exc

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info("Fine-tuned model bundle ready on %s.", resolved.device)
    return FinetunedModelBundle(
        model=model,
        tokenizer=tokenizer,
        base_model_name=base_model,
        adapter_path=adapter_path,
        resolved_device=resolved,
    )


# ---------------------------------------------------------------------------
# Conversation building + chat template
# ---------------------------------------------------------------------------


def build_conversation(
    question: str,
    context: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> List[Dict[str, str]]:
    """
    Build the system/user message list in the exact format the HDFC
    adapter was trained on: a system instruction, and a user turn of
    "Context:\n...\n\nQuestion:\n..." when context is given,
    or just the raw question otherwise.
    """
    if not question or not isinstance(question, str):
        raise ValueError("question must be a non-empty string.")

    q_clean = question.strip()
    c_clean = context.strip() if context and isinstance(context, str) else ""

    if c_clean:
        user_content = f"Context:\n{c_clean}\n\nQuestion:\n{q_clean}"
    else:
        user_content = q_clean

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def _render_generation_prompt(
    messages: List[Dict[str, str]], tokenizer: PreTrainedTokenizerBase
) -> str:
    """
    Render messages for GENERATION: add_generation_prompt=True opens the
    assistant turn for the model to continue (<|im_start|>assistant\n).
    """
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        # Fallback if tokenizer does not support chat template
        content_parts = []
        for m in messages:
            content_parts.append(f"{m.get('role', 'user').title()}: {m.get('content', '')}")
        content_parts.append("Assistant:")
        return "\n\n".join(content_parts)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_finetuned(
    bundle: FinetunedModelBundle,
    question: str,
    context: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    generation_config: Optional[GenerationConfig] = None,
) -> Dict[str, Any]:
    """
    Generate an HDFC-domain response for `question` using a fine-tuned
    model bundle from load_finetuned_model().

    Builds the chat-templated conversation, then delegates the actual
    tokenize -> model.generate() -> decode-new-tokens-only work to the
    existing, unmodified ai.inference.generator.generate() - the
    templated conversation string is passed as the "prompt" the tokenizer
    sees, so the model receives exactly the format it was trained on.

    Returns
    -------
    dict with keys: base_model, adapter_path, prompt (the raw question),
    context, response, latency_seconds, device, generation_config.

    Raises
    ------
    FinetunedGenerationError
        If generation fails, including GPU out-of-memory.
    """
    messages = build_conversation(question, context, system_prompt)
    templated_text = _render_generation_prompt(messages, bundle.tokenizer)

    config = generation_config or GenerationConfig()

    try:
        raw_result = generate(
            tokenizer=bundle.tokenizer,
            model=bundle.model,
            prompt=templated_text,
            model_name=bundle.base_model_name,
            device=bundle.resolved_device.device,
            generation_config=config,
        )
    except torch.cuda.OutOfMemoryError as exc:
        raise FinetunedGenerationError(
            f"Ran out of GPU memory during generation with "
            f"max_new_tokens={config.max_new_tokens}. Try a smaller "
            "--max-new-tokens value, or device='cpu'."
        ) from exc

    resp = raw_result["response"]
    if isinstance(resp, str) and "</think>" in resp:
        resp = resp.split("</think>")[-1].strip()

    return {
        "base_model": bundle.base_model_name,
        "adapter_path": str(bundle.adapter_path),
        "prompt": question,
        "context": context,
        "response": resp,
        "latency_seconds": raw_result["latency_seconds"],
        "device": raw_result["device"],
        "generation_config": raw_result["generation_config"],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai.inference.finetuned",
        description="Run inference with the fine-tuned HDFC Qwen3-0.6B LoRA adapter.",
    )
    parser.add_argument(
        "--prompt", type=str, required=True, help="User question for the HDFC assistant."
    )
    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Optional authoritative context to include alongside the question.",
    )
    parser.add_argument("--base-model", type=str, default=DEFAULT_BASE_MODEL, dest="base_model")
    parser.add_argument(
        "--adapter-path",
        type=str,
        default=str(DEFAULT_ADAPTER_PATH),
        dest="adapter_path",
        help="Path to the trained LoRA adapter directory.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to run on (default: auto).",
    )
    parser.add_argument(
        "--max-new-tokens", type=int, default=256, dest="max_new_tokens"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save a JSON artifact of the result.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns a process exit code."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        bundle = load_finetuned_model(
            base_model=args.base_model,
            adapter_path=args.adapter_path,
            device=args.device,
        )
    except FinetunedInferenceError as exc:
        logger.error("Failed to load fine-tuned model: %s", exc)
        return 1

    generation_config = GenerationConfig(max_new_tokens=args.max_new_tokens)

    try:
        result = generate_finetuned(
            bundle,
            question=args.prompt,
            context=args.context,
            generation_config=generation_config,
        )
    except FinetunedInferenceError as exc:
        logger.error("Generation failed: %s", exc)
        return 1

    print("\n=== HDFC Fine-tuned Inference ===")
    print(f"Base model:  {result['base_model']}")
    print(f"Adapter:     {result['adapter_path']}")
    print(f"Device:      {result['device']}")
    print(f"Latency:     {result['latency_seconds']}s")
    print(f"Prompt:      {result['prompt']}")
    print(f"Response:    {result['response']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {"timestamp": datetime.now(timezone.utc).isoformat(), **result}
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, ensure_ascii=False)
        print(f"Artifact:    {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(run())