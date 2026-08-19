"""
ai/tests/test_trainer.py

Unit tests for ai/training/trainer.py.

These tests do NOT download Qwen3-0.6B and do NOT run real training - the
SFTTrainer class is mocked throughout the offline tests. The one real,
opt-in training smoke test is gated behind RUN_TRAINING_SMOKE_TEST=1.

Run unit tests only (default, fast, offline):
    python -m pytest ai/tests/test_trainer.py -v -m "not integration"

Run the real training smoke test:
    RUN_TRAINING_SMOKE_TEST=1 python -m pytest \
        ai/tests/test_trainer.py -v -m integration
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import torch
import torch.nn as nn

from ai.training.config import TrainingConfig
from ai.training.trainer import (
    TrainingConfigError,
    TrainingExecutionError,
    TrainingResult,
    _build_sft_config,
    _gpu_allocated_mb,
    _peak_gpu_allocated_mb,
    _resolve_training_device,
    train_model,
)


# ---------------------------------------------------------------------------
# 1. Invalid configuration handling
# ---------------------------------------------------------------------------


class TestInvalidConfigurationHandling:
    @patch("ai.training.trainer.SFTTrainer")
    def test_invalid_config_raises_before_trainer_construction(
        self, mock_sft_trainer_cls
    ):
        config = TrainingConfig(learning_rate=-1.0)  # invalid per validate()
        model = nn.Linear(4, 4)
        tokenizer = MagicMock()
        dataset = MagicMock()

        with pytest.raises(TrainingConfigError):
            train_model(model, tokenizer, dataset, config)

        # The whole point of validating first is that we never even try
        # to construct the underlying trainer with a bad config.
        mock_sft_trainer_cls.assert_not_called()


# ---------------------------------------------------------------------------
# 2. GPU metric helpers (CPU-safe behavior)
# ---------------------------------------------------------------------------


class TestGpuMetricHelpers:
    @patch("torch.cuda.is_available", return_value=False)
    def test_gpu_allocated_mb_none_on_cpu(self, _mock_available):
        assert _gpu_allocated_mb() is None

    @patch("torch.cuda.is_available", return_value=False)
    def test_peak_gpu_allocated_mb_none_on_cpu(self, _mock_available):
        assert _peak_gpu_allocated_mb() is None

    @patch("torch.cuda.is_available", return_value=False)
    def test_reset_peak_gpu_memory_does_not_raise_on_cpu(self, _mock_available):
        from ai.training.trainer import _reset_peak_gpu_memory

        _reset_peak_gpu_memory()  # should be a silent no-op

    @patch("torch.cuda.max_memory_allocated", return_value=123 * 1024 * 1024)
    @patch("torch.cuda.is_available", return_value=True)
    def test_peak_gpu_allocated_mb_reports_value_on_cuda(
        self, _mock_available, _mock_peak
    ):
        assert _peak_gpu_allocated_mb() == 123.0

    def test_resolve_training_device_reads_model_parameters(self):
        model = nn.Linear(4, 4)  # parameters default to CPU
        assert _resolve_training_device(model) == "cpu"


# ---------------------------------------------------------------------------
# 3. SFTConfig construction (argument mapping)
# ---------------------------------------------------------------------------


class TestBuildSftConfig:
    def test_maps_training_config_fields_correctly(self, tmp_path):
        config = TrainingConfig()
        sft_config = _build_sft_config(
            config, tmp_path, device="cpu", dataset_text_field="text"
        )

        assert sft_config.output_dir == str(tmp_path)
        assert sft_config.num_train_epochs == config.num_train_epochs
        assert (
            sft_config.per_device_train_batch_size
            == config.per_device_train_batch_size
        )
        assert (
            sft_config.gradient_accumulation_steps
            == config.gradient_accumulation_steps
        )
        assert sft_config.learning_rate == config.learning_rate
        assert sft_config.seed == config.seed
        assert sft_config.max_length == config.max_seq_length
        assert sft_config.dataset_text_field == "text"
        assert sft_config.packing is False
        assert sft_config.gradient_checkpointing is False

    def test_fp16_enabled_only_on_cuda(self, tmp_path):
        config = TrainingConfig()

        cpu_config = _build_sft_config(config, tmp_path, "cpu", "text")
        cuda_config = _build_sft_config(config, tmp_path, "cuda", "text")

        assert cpu_config.fp16 is False
        assert cuda_config.fp16 is True

    def test_evaluation_and_checkpointing_disabled_for_smoke_test(self, tmp_path):
        config = TrainingConfig()
        sft_config = _build_sft_config(config, tmp_path, "cpu", "text")

        assert sft_config.eval_strategy == "no"
        assert sft_config.save_strategy == "no"


# ---------------------------------------------------------------------------
# 4. Result structure + CPU-safe metric behavior end-to-end (mocked trainer)
# ---------------------------------------------------------------------------


class TestTrainModelResultStructure:
    def _fake_model(self):
        model = nn.Linear(8, 8)
        # Freeze most params, leave a few trainable, mimicking a LoRA-style
        # partially-frozen model without needing a real PeftModel.
        for p in model.parameters():
            p.requires_grad = False
        model.weight.requires_grad = True
        return model

    @patch("ai.training.trainer.SFTTrainer")
    @patch("torch.cuda.is_available", return_value=False)
    def test_returns_well_formed_training_result(
        self, _mock_available, mock_sft_trainer_cls, tmp_path
    ):
        mock_trainer_instance = MagicMock()
        mock_trainer_instance.train.return_value = SimpleNamespace(
            metrics={"train_runtime": 12.34, "train_loss": 0.456},
            global_step=7,
        )
        mock_sft_trainer_cls.return_value = mock_trainer_instance

        config = TrainingConfig()
        model = self._fake_model()
        tokenizer = MagicMock()
        dataset = MagicMock()

        result = train_model(
            model, tokenizer, dataset, config, output_dir=tmp_path
        )

        assert isinstance(result, TrainingResult)
        assert result.output_dir == str(tmp_path)
        assert result.train_runtime == 12.34
        assert result.train_loss == 0.456
        assert result.global_step == 7
        assert result.trainable_parameters > 0
        assert result.total_parameters > result.trainable_parameters
        assert 0.0 < result.trainable_percentage < 100.0

        mock_trainer_instance.train.assert_called_once()
        mock_trainer_instance.save_model.assert_called_once_with(str(tmp_path))

    @patch("ai.training.trainer.SFTTrainer")
    @patch("torch.cuda.is_available", return_value=False)
    def test_gpu_fields_are_none_on_cpu(
        self, _mock_available, mock_sft_trainer_cls, tmp_path
    ):
        mock_trainer_instance = MagicMock()
        mock_trainer_instance.train.return_value = SimpleNamespace(
            metrics={"train_runtime": 1.0, "train_loss": 0.1}, global_step=1
        )
        mock_sft_trainer_cls.return_value = mock_trainer_instance

        config = TrainingConfig()
        model = self._fake_model()

        result = train_model(
            model, MagicMock(), MagicMock(), config, output_dir=tmp_path
        )

        assert result.peak_gpu_memory_mb is None
        assert result.gpu_allocated_before_mb is None
        assert result.gpu_allocated_after_mb is None

    @patch("ai.training.trainer.SFTTrainer")
    @patch("torch.cuda.is_available", return_value=False)
    def test_trainer_construction_failure_raises_execution_error(
        self, _mock_available, mock_sft_trainer_cls, tmp_path
    ):
        mock_sft_trainer_cls.side_effect = RuntimeError("boom")

        config = TrainingConfig()
        model = self._fake_model()

        with pytest.raises(TrainingExecutionError):
            train_model(
                model, MagicMock(), MagicMock(), config, output_dir=tmp_path
            )

    @patch("ai.training.trainer.SFTTrainer")
    @patch("torch.cuda.is_available", return_value=False)
    def test_train_failure_raises_execution_error(
        self, _mock_available, mock_sft_trainer_cls, tmp_path
    ):
        mock_trainer_instance = MagicMock()
        mock_trainer_instance.train.side_effect = RuntimeError("training exploded")
        mock_sft_trainer_cls.return_value = mock_trainer_instance

        config = TrainingConfig()
        model = self._fake_model()

        with pytest.raises(TrainingExecutionError):
            train_model(
                model, MagicMock(), MagicMock(), config, output_dir=tmp_path
            )


# ---------------------------------------------------------------------------
# Opt-in integration test (REAL first training run - no dataset assumptions)
# ---------------------------------------------------------------------------

RUN_SMOKE_TEST = os.environ.get("RUN_TRAINING_SMOKE_TEST") == "1"


@pytest.mark.integration
@pytest.mark.skipif(
    not RUN_SMOKE_TEST,
    reason=(
        "Opt-in real training smoke test. Set RUN_TRAINING_SMOKE_TEST=1 to "
        "run it (downloads Qwen/Qwen3-0.6B, attaches LoRA via the existing "
        "model.py, and runs one real optimizer step on 5 synthetic examples)."
    ),
)
def test_real_training_smoke_test():
    from datasets import Dataset
    from transformers import AutoTokenizer

    from ai.training.model import prepare_model

    # 1. Tiny synthetic in-memory dataset (~5 examples). Not Member 2's
    #    data, not read from disk, not hardcoded as "sample prompts" in
    #    trainer.py itself - generated here, in the test, for this test.
    synthetic_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Deposits earn interest based on the account tier.",
        "A savings account is a place to store money safely.",
        "Loans are approved after a credit assessment.",
        "This is a short synthetic sentence for a smoke test.",
    ]
    dataset = Dataset.from_dict({"text": synthetic_texts})

    # 2 & 3. Load the model through the existing preparation path and its
    #    tokenizer - no second model load, no second LoRA adapter.
    smoke_config = TrainingConfig(
        num_train_epochs=1.0,
        gradient_accumulation_steps=1,  # keep the smoke test fast/reliable
    )
    model = prepare_model(smoke_config)
    tokenizer = AutoTokenizer.from_pretrained(smoke_config.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "smoke_test_adapter"

        # 4. Run the very small training job.
        result = train_model(
            model, tokenizer, dataset, smoke_config, output_dir=output_dir
        )

        # 6. Report.
        print(
            f"train_loss={result.train_loss} "
            f"train_runtime={result.train_runtime:.2f}s "
            f"peak_gpu_memory_mb={result.peak_gpu_memory_mb} "
            f"trainable={result.trainable_parameters:,} "
            f"total={result.total_parameters:,}"
        )

        # 7. Assertions.
        assert result.train_runtime > 0
        assert result.trainable_parameters > 0
        assert result.trainable_parameters < result.total_parameters
        assert (output_dir / "adapter_config.json").exists()
        assert (output_dir / "adapter_model.safetensors").exists()