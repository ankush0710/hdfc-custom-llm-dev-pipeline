# Data and Model Lineage

## Unified data product

```text
Dataset: HDFC_Custom_LLM_All_11_Datasets_Unified_Suite
Pipeline version: v2.0-complete
Total records processed: 24,346
Duplicates removed: 4,725
PII redactions applied: 2,359
```

Final split:

```text
Train: 19,476
Validation: 2,434
Test: 2,436
```

## Model lineage

```text
Source datasets
  ↓
Cleaned/validated records
  ↓
Unified JSONL
  ↓
Train / Validation / Test
  ↓
Qwen/Qwen3-0.6B
  ↓
LoRA fine-tuning
  ↓
ai/artifacts/full_training/
  ↓
Held-out evaluation
  ↓
Runtime registration
  ↓
FastAPI inference
  ↓
Next.js frontend
```

Backend persistence should model:

```text
Dataset
→ DatasetVersion
→ PipelineRun
→ TrainingRun
→ Evaluation
→ ModelVersion
→ Deployment
```

Final HDFC model configuration:

```text
Base model: Qwen/Qwen3-0.6B
Training: LoRA
Adapter: ai/artifacts/full_training
Seed: 42
Epochs: 1
Learning rate: 2e-4
Max sequence length: 256
LoRA rank: 8
LoRA alpha: 16
LoRA dropout: 0.05
```
