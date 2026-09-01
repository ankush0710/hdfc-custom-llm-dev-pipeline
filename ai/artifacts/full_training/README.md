---
base_model: Qwen/Qwen3-0.6B
library_name: peft
pipeline_tag: text-generation
tags:
- qwen3
- lora
- sft
- peft
- transformers
- trl
- banking-domain
---

# HDFC Qwen3-0.6B LoRA Adapter

## Model Summary

This artifact contains the HDFC banking-domain LoRA adapter produced by supervised fine-tuning of `Qwen/Qwen3-0.6B`.

The adapter is intended to improve domain-specific instruction-following and structured response behavior for the HDFC Custom LLM Development Pipeline.

This repository separates model behavior adaptation from dynamic enterprise knowledge retrieval. The current artifact represents the model-adaptation component; it should not be interpreted as a complete production RAG implementation.

## Model Details

- **Base model:** `Qwen/Qwen3-0.6B`
- **Fine-tuning method:** LoRA / PEFT
- **PEFT type:** LORA
- **Task type:** CAUSAL_LM
- **PEFT version:** 0.20.0
- **Model family:** Qwen3
- **Pipeline task:** Text generation
- **Artifact directory:** `ai/artifacts/full_training/`

## Intended Use

The adapter is intended for controlled development and evaluation of HDFC banking-domain language-model behavior, including:

- domain-oriented question answering;
- instruction-following;
- structured generation;
- banking terminology and task patterns;
- evaluation and benchmarking within the project pipeline.

The model should be used only within approved application and security boundaries.

## Out-of-Scope Use

This artifact is not intended for:

- unrestricted general-purpose public chatbot deployment;
- autonomous financial decision-making;
- autonomous approval/rejection of banking transactions;
- unsupervised regulatory or compliance decisions;
- replacing qualified human reviewers in high-impact banking processes;
- use with confidential customer information without appropriate controls.

## Dataset Lineage

The current Qwen3 adapter is associated with the project dataset lineage:

**Release A**

| Split | Records |
|---|---:|
| Train | 19,476 |
| Validation | 2,434 |
| Test | 2,436 |
| Total | 24,346 |

The later expanded dataset release `v2.0.0-expanded` contains 59,346 records but was not used to retrain this adapter.

## Training Configuration

The saved training configuration in `training_args.bin` records the following primary parameters:

| Parameter | Value |
|---|---|
| Epochs | 1.0 |
| Learning rate | 0.0002 |
| Per-device train batch size | 1 |
| Gradient accumulation steps | 8 |
| Maximum sequence length | 256 |
| Seed | 42 |
| FP16 | true |
| Weight decay | 0.0 |
| Warmup steps | 0 |
| Optimizer | AdamW Torch Fused |
| Dataset text field | `text` |

## LoRA Configuration

The saved `adapter_config.json` records:

| Parameter | Value |
|---|---|
| PEFT type | LORA |
| LoRA rank (`r`) | 8 |
| LoRA alpha | 16 |
| LoRA dropout | 0.05 |
| Bias | none |
| Task type | CAUSAL_LM |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Inference mode | true |

## Artifact Contents

The adapter package contains:

- `adapter_config.json`
- `adapter_model.safetensors`
- `chat_template.jinja`
- `tokenizer.json`
- `tokenizer_config.json`
- `training_args.bin`
- this model card

## Evaluation

### AI Test Suite

The verified project AI test suite currently reports:

- **44 passed**
- **3 skipped**
- **0 failed**

The 44-test result includes the model-registry regression test added during final AI release hardening.

### Model Evaluation

Verified evaluation evidence for the current model includes:

| Metric | Result |
|---|---:|
| Test examples | 2,436 |
| Intent JSON validity | 1.0000 |
| Intent structured accuracy | 0.8290 |
| Answer accuracy | 1.0000 |
| Citation accuracy | 0.0000 |
| Policy flag accuracy | 1.0000 |
| Escalation accuracy | 1.0000 |
| Critical safety failures | 0 |
| Infrastructure errors | 0 |
| Average latency | ~3.83 seconds |

### Independent QA

The Member 4 QA suite reported:

- **28 tests executed**
- **27 automated PASS**
- **1 automated FAIL**
- **0 runtime errors**
- **Average latency: 12.606 seconds**

The failed case was `SFT-006`, related to groundedness/citation integrity.

The failure indicates that a generated citation was not supported by the supplied fixture context. The issue remains a known limitation requiring human semantic review.

## Known Limitations

The adapter should not be treated as a fully autonomous banking decision system.

Known limitations include:

1. Citation grounding is not guaranteed by the fine-tuned model alone.
2. Model outputs require application-level validation and policy controls.
3. High-impact banking decisions require appropriate human and system governance.
4. The model does not replace a governed retrieval system for frequently changing enterprise knowledge.
5. Evaluation results apply to the supplied project evaluation data and should not be generalized to all banking workloads.

## Safety and Governance

Production use should enforce:

- authenticated access;
- authorization and role controls;
- input validation;
- output validation;
- PII and sensitive-data controls;
- audit logging;
- model/version tracking;
- evaluation gates;
- approved deployment procedures;
- rollback capability.

This adapter should remain associated with its dataset lineage, training configuration, evaluation evidence, and registered model identity.

## Privacy

No production customer data should be introduced into the training or inference pipeline without appropriate authorization, privacy controls, and data-governance review.

Sensitive information should be minimized, protected, and handled according to the project's applicable privacy and security controls.

## Hardware and Reproducibility

The development environment used for local AI verification included:

- Python 3.11.9
- NVIDIA GeForce GTX 1650 Ti
- 4 GB VRAM

The saved training configuration provides reproducibility metadata including the random seed, optimizer, learning rate, batch size, gradient accumulation, sequence length, and LoRA configuration.

## Loading the Adapter

The adapter is a PEFT LoRA artifact and must be loaded together with its compatible base model:

`Qwen/Qwen3-0.6B`

The project inference layer is responsible for model loading and generation.

The expected project model identifier is:

`qwen3_0_6b`

## Release Validation

Before using this artifact, the project release validation script can be executed with:

```powershell
python ai/scripts/validate_release.py