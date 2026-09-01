import pytest
import torch


@pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="CUDA GPU is not available on this test runner",
)
def test_cuda_available():
    assert torch.cuda.is_available(), (
        "CUDA is not available. "
        "The AI environment requires a CUDA-enabled PyTorch installation."
    )


def test_gpu_memory():
    if torch.cuda.is_available():
        memory_gb = (
            torch.cuda.get_device_properties(0).total_memory
            / (1024**3)
        )

        assert memory_gb > 0