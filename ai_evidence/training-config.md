# Training Configuration

## Final Qwen3-0.6B LoRA configuration

```yaml
base_model: Qwen/Qwen3-0.6B
num_train_epochs: 1.0
learning_rate: 0.0002
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
max_seq_length: 256
lora_r: 8
lora_alpha: 16
lora_dropout: 0.05
seed: 42
```

## Validated development environment

```text
Python: 3.11
PyTorch: 2.10.0+cu126
CUDA used by PyTorch: 12.6
GPU: NVIDIA GeForce GTX 1650 Ti
VRAM: 4 GB
Compute capability: 7.5
```

## Final training snapshot

```text
Training records: 19,476
Global steps: 2,435
Train loss: 0.42605914677009443
Train runtime: ~30,406.9 s
Peak GPU memory: ~2175 MB
Trainable parameters: 2,293,760
Total parameters: 598,343,680
Trainable percentage: 0.3834%
```

## Current CLI options

```text
--dry-run
--max-train-samples N
--output-dir PATH
```

The local training code is not itself an HTTP API. FastAPI should orchestrate long-running training jobs.
