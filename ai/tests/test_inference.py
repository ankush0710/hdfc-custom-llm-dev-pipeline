"""
ai/tests/test_inference.py

Unit tests for the baseline inference engine (loader, generator, baseline).

These tests do NOT download any Hugging Face model and do NOT require
internet access — tokenizer/model objects are mocked throughout. Run them
with:

    python -m pytest ai/tests/test_inference.py -v

An opt-in integration test at the bottom actually downloads and runs the
smallest registry candidate (Qwen/Qwen3-0.6B). It is skipped by default;
set the environment variable RUN_INFERENCE_INTEGRATION_TESTS=1 to enable
it explicitly.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
import torch

from ai.inference.generator import GenerationConfig, generate
from ai.inference.loader import DeviceUnavailableError, resolve_device


# ---------------------------------------------------------------------------
# 1. Generation configuration validation
# ---------------------------------------------------------------------------


class TestGenerationConfigValidation:
    def test_defaults_are_valid(self):
        config = GenerationConfig()
        assert config.max_new_tokens > 0

    def test_rejects_non_positive_max_new_tokens(self):
        with pytest.raises(ValueError):
            GenerationConfig(max_new_tokens=0)
        with pytest.raises(ValueError):
            GenerationConfig(max_new_tokens=-5)

    def test_rejects_out_of_range_temperature(self):
        with pytest.raises(ValueError):
            GenerationConfig(temperature=0.0)
        with pytest.raises(ValueError):
            GenerationConfig(temperature=2.5)

    def test_rejects_out_of_range_top_p(self):
        with pytest.raises(ValueError):
            GenerationConfig(top_p=0.0)
        with pytest.raises(ValueError):
            GenerationConfig(top_p=1.5)


# ---------------------------------------------------------------------------
# 2. Invalid device handling
# ---------------------------------------------------------------------------


class TestDeviceResolution:
    def test_rejects_unknown_device_string(self):
        with pytest.raises(ValueError):
            resolve_device("tpu")

    @patch("torch.cuda.is_available", return_value=False)
    def test_cuda_requested_but_unavailable_raises(self, _mock_available):
        with pytest.raises(DeviceUnavailableError):
            resolve_device("cuda")

    @patch("torch.cuda.is_available", return_value=False)
    def test_auto_falls_back_to_cpu_when_no_cuda(self, _mock_available):
        resolved = resolve_device("auto")
        assert resolved.device == "cpu"
        assert resolved.dtype == torch.float32

    @patch("torch.cuda.is_available", return_value=True)
    def test_auto_prefers_cuda_when_available(self, _mock_available):
        resolved = resolve_device("auto")
        assert resolved.device == "cuda"
        assert resolved.dtype == torch.float16

    def test_cpu_always_succeeds(self):
        resolved = resolve_device("cpu")
        assert resolved.device == "cpu"
        assert resolved.dtype == torch.float32


# ---------------------------------------------------------------------------
# 3. Benchmark / generation result structure
# ---------------------------------------------------------------------------


def _mock_tokenizer_and_model():
    """Build a fake tokenizer + model pair sufficient to exercise generate()."""
    tokenizer = MagicMock()
    tokenizer.pad_token_id = 0
    tokenizer.eos_token_id = 0

    fake_inputs = {"input_ids": torch.tensor([[1, 2, 3]])}
    tokenizer_call_result = MagicMock()
    tokenizer_call_result.to.return_value = fake_inputs
    tokenizer.return_value = tokenizer_call_result
    tokenizer.decode.return_value = "mocked response"

    model = MagicMock()
    model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])

    return tokenizer, model


class TestGenerateResultStructure:
    def test_generate_returns_expected_keys(self):
        tokenizer, model = _mock_tokenizer_and_model()

        result = generate(
            tokenizer=tokenizer,
            model=model,
            prompt="Hello",
            model_name="fake/model",
            device="cpu",
            generation_config=GenerationConfig(max_new_tokens=5),
        )

        expected_keys = {
            "prompt",
            "response",
            "model_name",
            "generation_config",
            "latency_seconds",
            "device",
        }
        assert expected_keys.issubset(result.keys())
        assert result["model_name"] == "fake/model"
        assert result["device"] == "cpu"
        assert result["response"] == "mocked response"
        assert isinstance(result["latency_seconds"], float)
        assert isinstance(result["generation_config"], dict)

    def test_generate_rejects_empty_prompt(self):
        tokenizer, model = _mock_tokenizer_and_model()
        with pytest.raises(ValueError):
            generate(
                tokenizer=tokenizer,
                model=model,
                prompt="",
                model_name="fake/model",
                device="cpu",
            )

    def test_generate_uses_default_config_when_none_given(self):
        tokenizer, model = _mock_tokenizer_and_model()

        result = generate(
            tokenizer=tokenizer,
            model=model,
            prompt="Hello",
            model_name="fake/model",
            device="cpu",
        )

        assert result["generation_config"]["do_sample"] is False
        assert result["generation_config"]["seed"] == 42


# ---------------------------------------------------------------------------
# 4. Deterministic configuration defaults
# ---------------------------------------------------------------------------


class TestDeterministicDefaults:
    def test_default_config_matches_spec(self):
        config = GenerationConfig()
        assert config.temperature == 0.2
        assert config.top_p == 0.9
        assert config.do_sample is False
        assert config.seed == 42

    def test_same_seed_produces_same_torch_random_state(self):
        from ai.inference.generator import set_seed

        set_seed(42)
        first = torch.rand(3)
        set_seed(42)
        second = torch.rand(3)
        assert torch.equal(first, second)


# ---------------------------------------------------------------------------
# 5. Hardware-independent utility behavior
# ---------------------------------------------------------------------------


class TestHardwareIndependentUtilities:
    @patch("torch.cuda.is_available", return_value=False)
    def test_gpu_memory_snapshot_empty_on_cpu(self, _mock_available):
        from ai.inference.baseline import _gpu_memory_snapshot

        assert _gpu_memory_snapshot() == {}

    @patch("torch.cuda.is_available", return_value=False)
    def test_gpu_static_info_none_on_cpu(self, _mock_available):
        from ai.inference.baseline import _gpu_static_info

        info = _gpu_static_info()
        assert info["gpu_name"] is None
        assert info["gpu_memory_gb"] is None

    def test_read_default_model_name_missing_file_returns_none(self, tmp_path):
        from ai.inference.baseline import _read_default_model_name

        missing_path = tmp_path / "does_not_exist.yaml"
        assert _read_default_model_name(missing_path) is None

    def test_read_default_model_name_reads_expected_key(self, tmp_path):
        from ai.inference.baseline import _read_default_model_name

        config_path = tmp_path / "model_config.yaml"
        config_path.write_text("default_model: Qwen/Qwen3-0.6B\n", encoding="utf-8")
        assert _read_default_model_name(config_path) == "Qwen/Qwen3-0.6B"

    def test_default_output_path_is_deterministic_in_shape(self):
        from ai.inference.baseline import _default_output_path

        path = _default_output_path("Qwen/Qwen3-0.6B")
        assert path.name.startswith("Qwen__Qwen3-0.6B_")
        assert path.suffix == ".json"


# ---------------------------------------------------------------------------
# Opt-in integration test (real download + real GPU/CPU inference)
# ---------------------------------------------------------------------------

RUN_INTEGRATION = os.environ.get("RUN_INFERENCE_INTEGRATION_TESTS") == "1"


@pytest.mark.integration
@pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason=(
        "Opt-in integration test. Set RUN_INFERENCE_INTEGRATION_TESTS=1 to "
        "run it (this downloads and runs Qwen/Qwen3-0.6B)."
    ),
)
def test_baseline_end_to_end_smallest_model():
    from ai.inference.baseline import run

    exit_code = run(["--model", "Qwen/Qwen3-0.6B", "--max-new-tokens", "8"])
    assert exit_code == 0