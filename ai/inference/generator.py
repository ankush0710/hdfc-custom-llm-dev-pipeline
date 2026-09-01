"""
ai/inference/generator.py

Text generation logic, decoupled from model loading (see loader.py) and
CLI orchestration (see baseline.py).

Responsibilities
-----------------
- Accept an already-loaded tokenizer + model.
- Accept a prompt and a GenerationConfig.
- Generate deterministically by default (greedy decoding, fixed seed).
- Decode only the newly generated tokens, not the echoed prompt.
- Measure wall-clock latency.
- Return a structured result dictionary.

This module does NOT load models, parse CLI arguments, or write files.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

logger = logging.getLogger(__name__)

DEFAULT_SEED = 42


@dataclass
class GenerationConfig:
    """
    Configuration controlling how text is generated.

    Defaults are chosen for reproducible, deterministic benchmarking:
    greedy decoding (do_sample=False) with a fixed seed. temperature and
    top_p are always recorded in the result for reference, but are only
    actually applied to generation when do_sample=True.
    """

    max_new_tokens: int = 256
    temperature: float = 0.2
    top_p: float = 0.9
    do_sample: bool = False
    seed: int = DEFAULT_SEED

    def __post_init__(self) -> None:
        if self.max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be a positive integer.")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be in the range [0.0, 2.0].")
        if not (0.0 < self.top_p <= 1.0):
            raise ValueError("top_p must be in the range (0, 1.0].")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def set_seed(seed: int) -> None:
    """Seed torch (CPU and, if available, CUDA) for reproducible generation."""
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def generate(
    tokenizer: PreTrainedTokenizerBase,
    model: PreTrainedModel,
    prompt: str,
    model_name: str,
    device: str,
    generation_config: Optional[GenerationConfig] = None,
) -> Dict[str, Any]:
    """
    Generate a response for a single prompt.

    Parameters
    ----------
    tokenizer, model:
        Already-loaded tokenizer and model (see loader.ModelLoader).
    prompt:
        The input text prompt.
    model_name:
        Human-readable model identifier, recorded in the result so
        downstream tooling can compare a base model against a fine-tuned
        variant.
    device:
        The resolved device the model currently lives on ("cuda"/"cpu").
    generation_config:
        Generation parameters. Defaults to deterministic greedy decoding.

    Returns
    -------
    dict with keys: prompt, response, model_name, generation_config,
    latency_seconds, device.
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("prompt must be a non-empty string.")

    config = generation_config or GenerationConfig()
    set_seed(config.seed)

    encoded = tokenizer(prompt, return_tensors="pt")
    inputs = encoded.to(device)
    input_length = inputs["input_ids"].shape[1]

    eos_token_id = tokenizer.eos_token_id
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_token_id

    gen_kwargs: Dict[str, Any] = {
        "max_new_tokens": config.max_new_tokens,
        "do_sample": config.do_sample,
        "pad_token_id": pad_token_id,
        "eos_token_id": eos_token_id,
    }
    if config.do_sample:
        gen_kwargs["temperature"] = max(config.temperature, 0.01)
        gen_kwargs["top_p"] = config.top_p

    start = time.perf_counter()
    with torch.no_grad():
        output_ids = model.generate(**inputs, **gen_kwargs)
    latency_seconds = time.perf_counter() - start

    # Decode only the newly generated tokens, not the echoed prompt.
    new_tokens = output_ids[0][input_length:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    logger.info(
        "Generated %d new tokens in %.3fs", len(new_tokens), latency_seconds
    )

    return {
        "prompt": prompt,
        "response": response,
        "model_name": model_name,
        "generation_config": config.to_dict(),
        "latency_seconds": round(latency_seconds, 4),
        "device": device,
    }