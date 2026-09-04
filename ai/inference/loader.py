"""
ai/inference/loader.py

Model loading utilities for the baseline inference engine.

This module isolates *how* a Hugging Face causal/instruction model and its
tokenizer are loaded from *how* text is generated (see ``generator.py``) or
*how* the CLI orchestrates a benchmark run (see ``baseline.py``).

Responsibilities
-----------------
- Resolve the target device ("auto" / "cuda" / "cpu").
- Resolve a memory-conscious dtype for the resolved device.
- Load the tokenizer and model for a given Hugging Face model identifier.
- Fail early with clear, actionable error messages instead of raw CUDA
  tracebacks (e.g. out-of-memory, missing model, invalid device request).

This module intentionally does NOT:
- Perform generation (see generator.py).
- Parse CLI arguments (see baseline.py).
- Implement fine-tuning, quantization training, or LoRA/QLoRA.
- Hardcode any model identifier. The caller always supplies model_name.
"""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

logger = logging.getLogger(__name__)


def _hf_call_with_retry(fn, *args, **kwargs):
    """Executes a Hugging Face Hub download/call with token authentication and bounded exponential retry on 429 rate limits."""
    token = os.getenv("HF_TOKEN")
    if token and "token" not in kwargs:
        kwargs["token"] = token
    max_retries = 3
    base_delay = 1.5
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            err_str = str(exc)
            if ("429" in err_str or "Too Many Requests" in err_str) and attempt < max_retries - 1:
                delay = min(base_delay + random.uniform(0.1, 0.4), 8.0)
                logger.warning(
                    "Hugging Face returned 429 Too Many Requests on attempt %d/%d. Waiting %.1fs before retrying...",
                    attempt + 1, max_retries, delay
                )
                time.sleep(delay)
                base_delay = min(base_delay * 2.0, 6.0)
                continue
            raise


class ModelLoadError(RuntimeError):
    """Raised when a model or tokenizer cannot be loaded safely."""


class DeviceUnavailableError(ModelLoadError):
    """Raised when a requested device (e.g. 'cuda') is not available."""


class InsufficientMemoryError(ModelLoadError):
    """Raised when a model does not fit into the available GPU memory."""


@dataclass(frozen=True)
class ResolvedDevice:
    """The concrete device and dtype selected for a model."""

    device: str  # "cuda" or "cpu"
    dtype: torch.dtype


def resolve_device(requested_device: str = "auto") -> ResolvedDevice:
    """
    Resolve a requested device string into a concrete device + dtype.

    Parameters
    ----------
    requested_device:
        One of "auto", "cuda", or "cpu".
        - "auto" prefers CUDA when available, otherwise CPU.
        - "cuda" requires CUDA to be available; raises otherwise.
        - "cpu" always succeeds.

    Returns
    -------
    ResolvedDevice
        The concrete device ("cuda" or "cpu") and a memory-conscious dtype.

    Raises
    ------
    DeviceUnavailableError
        If "cuda" is requested but CUDA is not available.
    ValueError
        If an unrecognized device string is given.
    """
    if not isinstance(requested_device, str):
        raise ValueError(
            f"device must be a string, got {type(requested_device)!r}."
        )

    normalized = requested_device.lower().strip()

    if normalized not in {"auto", "cuda", "cpu"}:
        raise ValueError(
            f"Invalid device '{requested_device}'. "
            "Expected one of: auto, cuda, cpu."
        )

    cuda_available = torch.cuda.is_available()

    if normalized == "cuda" and not cuda_available:
        raise DeviceUnavailableError(
            "device='cuda' was requested but CUDA is not available on this "
            "machine (torch.cuda.is_available() returned False). Check your "
            "GPU drivers / CUDA install, or use device='cpu' or device='auto'."
        )

    if normalized == "auto":
        device = "cuda" if cuda_available else "cpu"
    else:
        device = normalized

    # Memory-conscious dtype strategy:
    # - On GPU (e.g. a 4GB-class card), float16 roughly halves memory usage
    #   versus float32 and is well supported on compute capability >= 7.0.
    # - On CPU, float16 kernels are poorly supported / slow for many ops,
    #   so float32 is used there instead.
    dtype = torch.float16 if device == "cuda" else torch.float32

    if device == "cpu":
        import os

        optimal_threads = min(8, os.cpu_count() or 4)

        if torch.get_num_threads() < optimal_threads:
            torch.set_num_threads(optimal_threads)

    logger.info(
        "Resolved device=%s dtype=%s (requested=%s)",
        device,
        dtype,
        requested_device,
    )

    return ResolvedDevice(device=device, dtype=dtype)


class ModelLoader:
    """
    Loads a Hugging Face tokenizer + causal LM for a given model identifier.

    Each ModelLoader instance caches its own tokenizer/model after the
    first load, so repeated calls to load()/load_model()/load_tokenizer()
    do not duplicate work or memory. Instances are not shared/cached
    globally by design, keeping ownership of loaded weights explicit.

    Example
    -------
    >>> loader = ModelLoader(model_name="Qwen/Qwen3-0.6B", device="auto")
    >>> tokenizer, model, resolved = loader.load()
    """

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        dtype: Optional[torch.dtype] = None,
        trust_remote_code: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        model_name:
            Hugging Face model identifier (e.g. "Qwen/Qwen3-0.6B"). Must be
            supplied by the caller; this class never hardcodes a model name.
        device:
            "auto", "cuda", or "cpu".
        dtype:
            Optional explicit torch dtype override. If None, a
            memory-conscious default is chosen based on the resolved
            device (float16 on CUDA, float32 on CPU).
        trust_remote_code:
            Passed through to `from_pretrained`. Defaults to False for
            safety; only set True for models you trust.
        """
        if not model_name or not isinstance(model_name, str):
            raise ValueError("model_name must be a non-empty string.")

        self.model_name = model_name
        self.requested_device = device
        self._dtype_override = dtype
        self.trust_remote_code = trust_remote_code

        self._tokenizer: Optional[PreTrainedTokenizerBase] = None
        self._model: Optional[PreTrainedModel] = None
        self._resolved: Optional[ResolvedDevice] = None

    def resolve(self) -> ResolvedDevice:
        """Resolve and cache the (device, dtype) pair for this loader."""
        if self._resolved is None:
            self._resolved = resolve_device(self.requested_device)
        return self._resolved

    def load_tokenizer(self) -> PreTrainedTokenizerBase:
        """Load (or return the cached) tokenizer for this loader's model."""
        if self._tokenizer is not None:
            return self._tokenizer

        try:
            tokenizer = _hf_call_with_retry(
                AutoTokenizer.from_pretrained,
                self.model_name,
                trust_remote_code=self.trust_remote_code,
            )
        except OSError as exc:
            raise ModelLoadError(
                f"Could not load tokenizer for '{self.model_name}'. Verify "
                "the model identifier is correct, that you have internet "
                "access (or a populated local cache), and that the "
                f"identifier exists on the Hugging Face Hub. Original error: {exc}"
            ) from exc

        # A causal LM needs a pad token for generation; many decoder-only
        # models don't define one by default, so fall back to eos_token.
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        self._tokenizer = tokenizer
        return tokenizer

    def load_model(self) -> PreTrainedModel:
        """
        Load (or return the cached) model for this loader's model name.

        Raises
        ------
        InsufficientMemoryError
            If CUDA reports an out-of-memory condition while loading or
            moving the model to the GPU. This is translated from the raw
            CUDA error into a clear, actionable message.
        ModelLoadError
            For any other model loading failure (bad identifier, missing
            local cache with no network, etc).
        """
        if self._model is not None:
            return self._model

        resolved = self.resolve()
        dtype = self._dtype_override or resolved.dtype

        try:
            model = _hf_call_with_retry(
                AutoModelForCausalLM.from_pretrained,
                self.model_name,
                dtype=dtype,
                low_cpu_mem_usage=True,
                trust_remote_code=self.trust_remote_code,
            )
        except OSError as exc:
            raise ModelLoadError(
                f"Could not load model weights for '{self.model_name}'. "
                "Verify the model identifier is correct, that you have "
                "internet access (or a populated local cache), and that the "
                f"identifier exists on the Hugging Face Hub. Original error: {exc}"
            ) from exc
        except torch.cuda.OutOfMemoryError as exc:
            raise InsufficientMemoryError(
                f"Ran out of GPU memory while loading '{self.model_name}' "
                f"with dtype={dtype}. This GPU likely does not have enough "
                "VRAM for this model at this precision. Try a smaller "
                "model from the registry, or explicitly pass device='cpu' "
                "to fall back to CPU inference."
            ) from exc

        try:
            if resolved.device == "cuda":
                model = model.to(resolved.device)
        except torch.cuda.OutOfMemoryError as exc:
            raise InsufficientMemoryError(
                f"Ran out of GPU memory moving '{self.model_name}' to CUDA "
                f"(dtype={dtype}). This model likely does not fit in the "
                "available VRAM. Try a smaller model, or use device='cpu'."
            ) from exc

        model.eval()
        self._model = model
        return model

    def load(
        self,
    ) -> Tuple[PreTrainedTokenizerBase, PreTrainedModel, ResolvedDevice]:
        """
        Convenience method: load tokenizer + model + resolved device info.

        Returns
        -------
        tuple(PreTrainedTokenizerBase, PreTrainedModel, ResolvedDevice)
        """
        tokenizer = self.load_tokenizer()
        model = self.load_model()
        resolved = self.resolve()
        return tokenizer, model, resolved