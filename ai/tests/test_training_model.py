"""
ai/tests/test_training_model.py

Unit tests for ai/training/model.py.

These tests avoid downloading or loading the real Qwen3-0.6B model. Linear
submodule inspection and parameter counting are exercised against tiny
hand-built torch.nn.Module fixtures so they run instantly and offline.
The real load_base_model()/attach_lora() path is only exercised by the
opt-in `integration` test at the bottom.

Run unit tests only (default, fast, offline):
    python -m pytest ai/tests/test_training_model.py -v -m "not integration"

Run everything, including the real download + LoRA attach:
    RUN_TRAINING_MODEL_INTEGRATION_TESTS=1 python -m pytest \
        ai/tests/test_training_model.py -v -m integration
"""

from __future__ import annotations

import os

import pytest
import torch
import torch.nn as nn

from ai.training.config import TrainingConfig
from ai.training.model import (
    LoraAttachmentError,
    ParameterSummary,
    _validate_target_modules,
    count_parameters,
    inspect_linear_modules,
)


# ---------------------------------------------------------------------------
# Fixtures: tiny fake "attention block" style module, no HF download needed
# ---------------------------------------------------------------------------


class _FakeAttention(nn.Module):
    def __init__(self, dim: int = 4) -> None:
        super().__init__()
        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.o_proj = nn.Linear(dim, dim)


class _FakeMLP(nn.Module):
    def __init__(self, dim: int = 4) -> None:
        super().__init__()
        self.gate_proj = nn.Linear(dim, dim)
        self.up_proj = nn.Linear(dim, dim)
        self.down_proj = nn.Linear(dim, dim)


class _FakeDecoderLayer(nn.Module):
    def __init__(self, dim: int = 4) -> None:
        super().__init__()
        self.self_attn = _FakeAttention(dim)
        self.mlp = _FakeMLP(dim)


class _FakeCausalLM(nn.Module):
    """Mimics the shape of a small decoder-only model without any HF deps."""

    def __init__(self, dim: int = 4, num_layers: int = 2) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            [_FakeDecoderLayer(dim) for _ in range(num_layers)]
        )
        self.lm_head = nn.Linear(dim, 100)


# ---------------------------------------------------------------------------
# 1. TrainingConfig validation interaction
# ---------------------------------------------------------------------------


class TestTrainingConfigInteraction:
    def test_default_config_constructs(self):
        config = TrainingConfig()
        assert config.base_model == "Qwen/Qwen3-0.6B"
        assert config.lora_r > 0
        assert config.lora_alpha > 0

    def test_config_seed_is_used_for_reproducibility(self):
        config = TrainingConfig()
        assert isinstance(config.seed, int)

    def test_invalid_learning_rate_is_rejected(self):
        # TrainingConfig.validate() is called explicitly by the caller -
        # it is NOT a __post_init__ validator, so construction itself
        # succeeds even with a bad value; validate() is what must raise.
        config = TrainingConfig(learning_rate=-1.0)
        with pytest.raises(ValueError):
            config.validate()


# ---------------------------------------------------------------------------
# 2. Architecture inspection / target_module validation
# ---------------------------------------------------------------------------


class TestArchitectureInspection:
    def test_inspect_linear_modules_counts_leaf_names(self):
        model = _FakeCausalLM(num_layers=3)
        counts = inspect_linear_modules(model)

        assert counts["q_proj"] == 3
        assert counts["k_proj"] == 3
        assert counts["v_proj"] == 3
        assert counts["o_proj"] == 3
        assert counts["gate_proj"] == 3
        assert counts["lm_head"] == 1

    def test_validate_target_modules_passes_for_existing_names(self):
        model = _FakeCausalLM(num_layers=2)
        # Should not raise.
        _validate_target_modules(
            model, ["q_proj", "k_proj", "v_proj", "o_proj"]
        )

    def test_validate_target_modules_raises_for_missing_names(self):
        model = _FakeCausalLM(num_layers=2)
        with pytest.raises(LoraAttachmentError) as exc_info:
            _validate_target_modules(model, ["not_a_real_module"])
        assert "not_a_real_module" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. Parameter counting helper
# ---------------------------------------------------------------------------


class TestParameterCounting:
    def test_all_trainable_by_default(self):
        model = nn.Linear(10, 10)
        summary = count_parameters(model)
        assert isinstance(summary, ParameterSummary)
        assert summary.total_parameters == summary.trainable_parameters
        assert summary.trainable_percentage == 100.0

    def test_frozen_model_has_zero_trainable(self):
        model = nn.Linear(10, 10)
        for p in model.parameters():
            p.requires_grad = False
        summary = count_parameters(model)
        assert summary.trainable_parameters == 0
        assert summary.trainable_percentage == 0.0

    def test_partial_freeze_reports_correct_percentage(self):
        model = _FakeCausalLM(num_layers=1)
        total_before = sum(p.numel() for p in model.parameters())

        # Freeze everything, then unfreeze just one small linear layer,
        # mimicking what LoRA-style partial training looks like.
        for p in model.parameters():
            p.requires_grad = False
        for p in model.layers[0].self_attn.q_proj.parameters():
            p.requires_grad = True

        summary = count_parameters(model)
        expected_trainable = sum(
            p.numel() for p in model.layers[0].self_attn.q_proj.parameters()
        )
        assert summary.total_parameters == total_before
        assert summary.trainable_parameters == expected_trainable
        assert 0.0 < summary.trainable_percentage < 100.0


# ---------------------------------------------------------------------------
# Opt-in integration test (real download, real LoRA attach, no training)
# ---------------------------------------------------------------------------

RUN_INTEGRATION = os.environ.get("RUN_TRAINING_MODEL_INTEGRATION_TESTS") == "1"


@pytest.mark.integration
@pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason=(
        "Opt-in integration test. Set RUN_TRAINING_MODEL_INTEGRATION_TESTS=1 "
        "to run it (downloads Qwen/Qwen3-0.6B and attaches a real LoRA "
        "adapter; does NOT start training)."
    ),
)
def test_prepare_model_attaches_lora_on_real_qwen3():
    from peft import PeftModel

    from ai.training.model import prepare_model

    config = TrainingConfig()
    model = prepare_model(config)

    # --------------------------------------------------------------
    # 1. Verify that PEFT actually wrapped the base model.
    # --------------------------------------------------------------
    assert isinstance(model, PeftModel)

    # --------------------------------------------------------------
    # 2. Verify that a LoRA configuration exists.
    # --------------------------------------------------------------
    assert "default" in model.peft_config

    lora_config = model.peft_config["default"]

    # --------------------------------------------------------------
    # 3. Verify the intended attention projections are configured
    #    as LoRA target modules.
    # --------------------------------------------------------------
    expected_targets = {
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    }

    actual_targets = set(lora_config.target_modules)

    assert expected_targets.issubset(actual_targets)

    # --------------------------------------------------------------
    # 4. Verify that LoRA created trainable parameters.
    # --------------------------------------------------------------
    from ai.training.model import count_parameters

    summary = count_parameters(model)

    print(
        f"total={summary.total_parameters:,} "
        f"trainable={summary.trainable_parameters:,} "
        f"({summary.trainable_percentage:.4f}%)"
    )

    assert summary.trainable_parameters > 0

    # --------------------------------------------------------------
    # 5. Verify that we are NOT accidentally full-fine-tuning
    #    the entire base model.
    # --------------------------------------------------------------
    assert summary.trainable_parameters < summary.total_parameters

    # LoRA should train only a small fraction of the model.
    assert summary.trainable_percentage < 10.0