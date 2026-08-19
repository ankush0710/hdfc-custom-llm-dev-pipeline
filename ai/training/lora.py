from __future__ import annotations

from peft import LoraConfig

from ai.training.config import TrainingConfig


def build_lora_config(config: TrainingConfig) -> LoraConfig:
    """
    Build the PEFT LoRA configuration used to adapt the base model.
    """

    config.validate()

    return LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
        ],
    )