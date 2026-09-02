# Environment

## Validated local environment

```text
Python 3.11
PyTorch 2.10.0+cu126
CUDA 12.6
NVIDIA GeForce GTX 1650 Ti
4 GB VRAM
Compute capability 7.5
```

Runtime dependency families:

```text
torch
transformers
peft
datasets
accelerate
PyYAML
safetensors
```

The project root `requirements-lock.txt` should be treated as the authoritative dependency lock file when available.

Qwen/Qwen3-0.6B inference was smoke-tested successfully on CUDA on the validated development machine. Do not interpret this as evidence that every registry model was independently smoke-tested on that machine.

The local environment is a development/test setup, not a production deployment recommendation.
