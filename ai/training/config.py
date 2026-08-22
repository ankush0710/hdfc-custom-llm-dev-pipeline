from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingConfig:
    # --------------------------------------------------
    # Model
    # --------------------------------------------------
    base_model: str = "Qwen/Qwen3-0.6B"

    # --------------------------------------------------
    # Dataset
    # --------------------------------------------------
    dataset_path: Path = Path("data/training")

    # --------------------------------------------------
    # Output
    # --------------------------------------------------
    output_dir: Path = Path("ai/artifacts/fine_tuned")

    # --------------------------------------------------
    # Training
    # --------------------------------------------------
    num_train_epochs: float = 1.0
    learning_rate: float = 2e-4

    # Small GPU-friendly defaults
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 8

    # Keep this conservative for 4 GB VRAM
    max_seq_length: int = 256

    # --------------------------------------------------
    # LoRA
    # --------------------------------------------------
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05

    # --------------------------------------------------
    # Reproducibility
    # --------------------------------------------------
    seed: int = 42

    def validate(self) -> None:
        if not self.base_model:
            raise ValueError("base_model must not be empty.")

        if self.num_train_epochs <= 0:
            raise ValueError("num_train_epochs must be positive.")

        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")

        if self.per_device_train_batch_size <= 0:
            raise ValueError(
                "per_device_train_batch_size must be positive."
            )

        if self.gradient_accumulation_steps <= 0:
            raise ValueError(
                "gradient_accumulation_steps must be positive."
            )

        if self.max_seq_length <= 0:
            raise ValueError("max_seq_length must be positive.")

        if self.lora_r <= 0:
            raise ValueError("lora_r must be positive.")

        if self.lora_alpha <= 0:
            raise ValueError("lora_alpha must be positive.")

        if not 0.0 <= self.lora_dropout < 1.0:
            raise ValueError(
                "lora_dropout must be in the range [0, 1)."
            )