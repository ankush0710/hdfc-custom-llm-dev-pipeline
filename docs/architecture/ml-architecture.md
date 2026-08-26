# ML Architecture

## 1. Purpose

The ML layer provides the model training, fine-tuning, model selection, inference, and evaluation components of the HDFC Custom LLM development pipeline.

The design separates training, model registration, inference, and evaluation so that the backend can consume a stable AI inference boundary without duplicating model-loading logic.

## 2. ML Pipeline

```text
Banking Data
     |
     v
Data Preparation / Validation
     |
     v
Training / Validation / Test Splits
     |
     v
Base Model
Qwen/Qwen3-0.6B
     |
     v
LoRA Fine-Tuning
     |
     v
HDFC LoRA Adapter
     |
     v
Model Registry
     |
     +----------------------------+
     |                            |
     v                            v
Fine-Tuned Model              Baseline Models
Qwen3-0.6B + LoRA             Qwen2.5-1.5B-Instruct
                               SmolLM2-1.7B-Instruct
     |
     v
Inference Service
     |
     v
Evaluation / QA
```

## 3. Supported Models

| Model ID | Model | Parameters | Role |
|---|---|---:|---|
| `qwen3_0_6b` | Qwen/Qwen3-0.6B | 0.6B | Primary HDFC fine-tuned model |
| `qwen2_5_1_5b_instruct` | Qwen/Qwen2.5-1.5B-Instruct | 1.54B | Baseline |
| `smollm2_1_7b_instruct` | HuggingFaceTB/SmolLM2-1.7B-Instruct | 1.7B | Baseline |

The model registry is maintained in `ai/config/model_registry.yaml`.

## 4. Fine-Tuning Strategy

The primary HDFC model uses:

- Base model: `Qwen/Qwen3-0.6B`
- Fine-tuning method: LoRA / PEFT
- Objective: supervised fine-tuning for banking-domain instruction generation

The final LoRA adapter is stored under:

```text
ai/artifacts/full_training/
```

## 5. Dataset Lineage

### Release A — current model training lineage

| Split | Records |
|---|---:|
| Train | 19,476 |
| Validation | 2,434 |
| Test | 2,436 |
| Total | 24,346 |

### Release B — expanded frozen master release

`v2.0.0-expanded`

| Split | Records |
|---|---:|
| Train | 47,476 |
| Validation | 5,934 |
| Test | 5,936 |
| Total | 59,346 |

The expanded release is the newer frozen master dataset and was not used to retrain the current Qwen3 adapter.

## 6. Model Registry

The registry provides a common description of supported models, including:

- model ID and name
- model family
- parameter count
- task
- license
- priority
- enabled status
- local-test availability
- cloud-training availability

## 7. Inference Layer

The AI inference layer is responsible for:

1. selecting a registered model;
2. loading the required base model;
3. loading the HDFC LoRA adapter when Qwen3 fine-tuning is selected;
4. generating text;
5. producing structured responses;
6. supporting baseline/fine-tuned comparison;
7. evaluation and runtime checks.

Relevant implementation areas:

```text
ai/inference/
ai/models/
ai/config/
```

The backend should consume the existing inference/service boundary rather than implementing a second model-loading mechanism.

## 8. Evaluation and QA

The AI test suite has been verified locally with:

```text
43 passed
3 skipped
0 failed
```

The separate Member 4 GPU QA execution covered:

```text
28 total tests
28 completed
0 runtime errors
27 automated PASS
1 automated FAIL
Average latency: 12.606 seconds
```

The single automated failure was SFT-006, related to groundedness/citation integrity. The model generated the unsupported citation `HDFC Master Policy Doc #436`. Human semantic review remains required for final QA sign-off.

## 9. Hardware Verification

The local GPU verification environment used:

- NVIDIA GeForce GTX 1650 Ti
- 4 GB VRAM
- Python 3.11.9

## 10. Reproducibility

The final adapter and supporting configuration are retained under:

```text
ai/artifacts/full_training/
ai/config/
```

This preserves base-model identity, adapter identity, model-selection metadata, and training/evaluation configuration needed for reproducibility.

## 11. Summary

```text
Dataset
   |
   v
Validated Splits
   |
   v
Qwen3-0.6B
   |
   v
LoRA Fine-Tuning
   |
   v
HDFC Adapter
   |
   v
Model Registry
   |
   v
Inference Service
   |
   +----> Baseline Comparison
   |
   +----> Evaluation
   |
   +----> Backend Integration
```
