"""
ai/training/trainer.py

Training execution layer for a controlled smoke test. This module runs a
short SFT job using an ALREADY-PREPARED PEFT model (see
ai.training.model.prepare_model) and a caller-supplied dataset. It does
not load a model, build a LoRA adapter, load Member 2's dataset, or
implement evaluation.

Responsibilities
-----------------
- Validate the supplied TrainingConfig before doing any work.
- Build an SFTConfig from TrainingConfig, using the current TRL 1.9.2 API
  (processing_class=, SFTConfig.max_length, no tokenizer=/max_seq_length=
  on the trainer constructor - both were removed/renamed upstream).
- Run trl.SFTTrainer.train() using the model exactly as passed in - no
  second model load, no second LoraConfig/get_peft_model call.
- Record GPU memory before/after/peak, safely returning None on CPU-only
  systems.
- Save only the adapter (via trainer.save_model(), which on a PeftModel
  saves adapter weights, not the frozen base model).
- Return a structured TrainingResult.

This module does NOT:
- load or transform Member 2's dataset
- build dataset.py, train.py, or evaluation.py
- expose a CLI or API
- rewrite ai/training/model.py or ai/training/lora.py

Usage
-----
    from ai.training.config import TrainingConfig
    from ai.training.model import prepare_model
    from ai.training.trainer import train_model

    config = TrainingConfig()
    model = prepare_model(config)          # base model + LoRA, already done
    tokenizer = ...                        # caller-supplied
    dataset = ...                          # caller-supplied HF Dataset

    result = train_model(model, tokenizer, dataset, config)
    print(result.to_dict())
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase, TrainerCallback
from trl import SFTConfig, SFTTrainer

from ai.training.config import TrainingConfig
from ai.training.model import count_parameters

logger = logging.getLogger(__name__)


class TrainingProgressCallback(TrainerCallback):
    """Callback to report step-level training progress percentage and check cancellation."""

    def __init__(
        self,
        on_progress: Optional[Any] = None,
        should_stop: Optional[Any] = None,
        start_pct: int = 20,
        end_pct: int = 95,
    ):
        super().__init__()
        self.on_progress = on_progress
        self.should_stop = should_stop
        self.start_pct = start_pct
        self.end_pct = end_pct

    def on_step_end(self, args, state, control, **kwargs):
        # 1. Check for cancellation request
        if self.should_stop:
            try:
                if self.should_stop():
                    logger.info(
                        "TRAINER CALLBACK: Stop requested at step %d/%d. Setting control.should_training_stop = True.",
                        state.global_step,
                        state.max_steps or 0,
                    )
                    control.should_training_stop = True
                    return control
            except Exception as exc:
                logger.exception("Trainer callback should_stop check failed: %s", exc)

        # 2. Extract real metrics from the trainer state's log history
        loss: Optional[float] = None
        lr: Optional[float] = None
        if state.log_history:
            last_log = state.log_history[-1]
            raw_loss = last_log.get("loss")
            raw_lr = last_log.get("learning_rate")
            if raw_loss is not None:
                try:
                    loss = float(raw_loss)
                except (TypeError, ValueError):
                    pass
            if raw_lr is not None:
                try:
                    lr = float(raw_lr)
                except (TypeError, ValueError):
                    pass

        # 3. Progress update — sample every N steps (max ~100 points) + always on last step
        if state.max_steps and state.max_steps > 0:
            ratio = min(1.0, max(0.0, state.global_step / state.max_steps))
            current_pct = int(self.start_pct + (self.end_pct - self.start_pct) * ratio)

            # Fire at least every 5 steps so early progress is visible
            stride = max(1, min(5, state.max_steps // 100))
            is_sampled_step = (state.global_step % stride == 0)
            is_last_step = (state.global_step >= state.max_steps)

            logger.info(
                "TRAINER CALLBACK: pct=%d, step=%d/%d, loss=%s, lr=%s",
                current_pct,
                state.global_step,
                state.max_steps,
                loss,
                lr,
            )

            if self.on_progress and (is_sampled_step or is_last_step):
                try:
                    self.on_progress(
                        current_pct,
                        state.global_step,
                        state.max_steps,
                        loss=loss,
                        lr=lr,
                    )
                except Exception as exc:
                    logger.exception("Progress callback notification failed: %s", exc)

        return control



class TrainerError(RuntimeError):
    """Base exception for training execution failures."""


class TrainingConfigError(TrainerError):
    """Raised when the supplied TrainingConfig fails validate()."""


class TrainingExecutionError(TrainerError):
    """Raised when the underlying TRL/Transformers trainer fails to run."""


# ---------------------------------------------------------------------------
# GPU memory helpers (CPU-safe: never raise, never require CUDA)
# ---------------------------------------------------------------------------


def _gpu_allocated_mb() -> Optional[float]:
    """Current allocated GPU memory in MB, or None on CPU-only systems."""
    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.memory_allocated() / (1024**2), 2)


def _reset_peak_gpu_memory() -> None:
    """Reset CUDA peak memory stats; a no-op on CPU-only systems."""
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def _peak_gpu_allocated_mb() -> Optional[float]:
    """Peak allocated GPU memory in MB since the last reset, or None on CPU."""
    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.max_memory_allocated() / (1024**2), 2)


def _resolve_training_device(model: torch.nn.Module) -> str:
    """Infer 'cuda' or 'cpu' from where the (already-loaded) model lives."""
    try:
        return next(model.parameters()).device.type
    except StopIteration:
        return "cpu"


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrainingResult:
    """Structured outcome of a train_model() run."""

    output_dir: str
    train_runtime: float
    train_loss: Optional[float]
    global_step: Optional[int]
    peak_gpu_memory_mb: Optional[float]
    gpu_allocated_before_mb: Optional[float]
    gpu_allocated_after_mb: Optional[float]
    trainable_parameters: int
    total_parameters: int
    trainable_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# SFTConfig construction (current TRL 1.9.2 API)
# ---------------------------------------------------------------------------


def _build_sft_config(
    config: TrainingConfig,
    output_dir: Path,
    device: str,
    dataset_text_field: str,
) -> SFTConfig:
    """
    Build an SFTConfig for a conservative, single-GPU-friendly smoke test.

    Notes on TRL 1.9.2 API (verified, not assumed from older tutorials):
    - `tokenizer=`/`max_seq_length=` are no longer accepted directly by
      SFTTrainer; the tokenizer goes through `processing_class=` on the
      trainer, and sequence length is `max_length` here on SFTConfig.
    - `dataset_text_field` and `packing` also live on SFTConfig, not on
      the trainer constructor.
    """
    return SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        seed=config.seed,
        max_length=config.max_seq_length,
        dataset_text_field=dataset_text_field,
        packing=False,
        # Gradient checkpointing is already enabled on the model by
        # ai.training.model.prepare_model(); re-enabling it here via
        # TrainingArguments risks a conflicting reentrant-checkpointing
        # configuration, so it is explicitly left off at this layer.
        gradient_checkpointing=False,
        fp16=(device == "cuda"),
        bf16=False,
        eval_strategy="no",
        save_strategy="no",
        logging_strategy="steps",
        logging_steps=1,
        report_to="none",
    )


# ---------------------------------------------------------------------------
# Training execution
# ---------------------------------------------------------------------------


def train_model(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    dataset: Any,
    config: TrainingConfig,
    output_dir: Optional[Union[str, Path]] = None,
    dataset_text_field: str = "text",
    callbacks: Optional[List[Any]] = None,
) -> TrainingResult:
    """
    Run a short SFT training job on an already-prepared PEFT model.

    Parameters
    ----------
    model:
        An already-loaded, LoRA-attached model (see
        ai.training.model.prepare_model). This function does not load a
        model or attach an adapter; it trains exactly what it is given.
    tokenizer:
        Tokenizer matching `model`, supplied by the caller.
    dataset:
        A Hugging Face Dataset (or compatible object) supplied by the
        caller. Not created, loaded, or transformed by this module.
    config:
        TrainingConfig. Validated via config.validate() before any
        training work begins.
    output_dir:
        Where to save the trained adapter. Defaults to config.output_dir.
    dataset_text_field:
        Name of the text column SFTTrainer should read from `dataset`.
        Defaults to "text"; adjust if the caller's dataset uses a
        different column name. Never hardcoded to specific sample content.

    Returns
    -------
    TrainingResult

    Raises
    ------
    TrainingConfigError
        If config.validate() raises.
    TrainingExecutionError
        If the underlying SFTTrainer fails to construct or train
        (including GPU out-of-memory, translated into a clear message).
    """
    try:
        config.validate()
    except ValueError as exc:
        raise TrainingConfigError(f"Invalid TrainingConfig: {exc}") from exc

    resolved_output_dir = Path(output_dir) if output_dir else Path(config.output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    device = _resolve_training_device(model)
    logger.info("Training on device=%s, output_dir=%s", device, resolved_output_dir)

    gpu_before = _gpu_allocated_mb()
    _reset_peak_gpu_memory()

    sft_config = _build_sft_config(
        config, resolved_output_dir, device, dataset_text_field
    )

    try:
        trainer = SFTTrainer(
            model=model,
            args=sft_config,
            train_dataset=dataset,
            processing_class=tokenizer,
            callbacks=callbacks,
        )
    except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
        raise TrainingExecutionError(
            f"Failed to construct SFTTrainer: {exc}"
        ) from exc

    start = time.perf_counter()
    try:
        train_output = trainer.train()
    except torch.cuda.OutOfMemoryError as exc:
        raise TrainingExecutionError(
            "Ran out of GPU memory during training. This 4GB GPU cannot "
            "sustain the current batch_size/gradient_accumulation_steps/"
            "max_seq_length combination - reduce max_seq_length or "
            f"gradient_accumulation_steps in TrainingConfig. Original error: {exc}"
        ) from exc
    except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
        raise TrainingExecutionError(f"Training failed: {exc}") from exc
    wall_runtime = time.perf_counter() - start

    metrics = getattr(train_output, "metrics", {}) or {}
    train_runtime = float(metrics.get("train_runtime", wall_runtime))
    train_loss = metrics.get("train_loss")
    global_step = getattr(train_output, "global_step", None) or metrics.get(
        "global_step"
    )

    try:
        trainer.save_model(str(resolved_output_dir))
    except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
        raise TrainingExecutionError(
            f"Training completed but saving the adapter failed: {exc}"
        ) from exc

    gpu_after = _gpu_allocated_mb()
    peak_gpu = _peak_gpu_allocated_mb()

    summary = count_parameters(model)
    logger.info(
        "Training complete: runtime=%.2fs loss=%s trainable=%s/%s (%.4f%%)",
        train_runtime,
        train_loss,
        f"{summary.trainable_parameters:,}",
        f"{summary.total_parameters:,}",
        summary.trainable_percentage,
    )

    return TrainingResult(
        output_dir=str(resolved_output_dir),
        train_runtime=train_runtime,
        train_loss=float(train_loss) if train_loss is not None else None,
        global_step=int(global_step) if global_step is not None else None,
        peak_gpu_memory_mb=peak_gpu,
        gpu_allocated_before_mb=gpu_before,
        gpu_allocated_after_mb=gpu_after,
        trainable_parameters=summary.trainable_parameters,
        total_parameters=summary.total_parameters,
        trainable_percentage=summary.trainable_percentage,
    )