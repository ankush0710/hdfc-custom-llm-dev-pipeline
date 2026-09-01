# Model Registry

| ID | Name | HDFC fine-tuned | Adapter |
|---|---|---:|---|
| `qwen3_0_6b` | Qwen/Qwen3-0.6B | yes | `ai/artifacts/full_training` |
| `qwen2_5_1_5b_instruct` | Qwen/Qwen2.5-1.5B-Instruct | no | none |
| `smollm2_1_7b_instruct` | HuggingFaceTB/SmolLM2-1.7B-Instruct | no | none |

Only Qwen3 is HDFC fine-tuned.

The explicit fine-tuned mapping currently lives in `ai/inference/service.py` because `model_registry.yaml` does not contain adapter fields.

The runtime keeps one model resident at a time because the validated development machine has 4 GB VRAM.
