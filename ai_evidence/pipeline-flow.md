# Pipeline Flow

## Actual ML lifecycle

```text
Raw Dataset Ingestion
        ↓
Dataset Cleaning / Standardization
        ↓
PII Detection / Redaction
        ↓
Duplicate Handling
        ↓
Task Normalization / Formatting
        ↓
Train / Validation / Test Split
        ↓
Qwen3-0.6B LoRA Fine-tuning
        ↓
Held-out Evaluation
        ↓
Model Validation
        ↓
Model Artifact Generation
        ↓
Model Registry / Runtime Selection
        ↓
Inference Service
        ↓
FastAPI Backend
        ↓
Next.js Frontend
```

## Step definitions

| Step | Purpose | Input | Output | Failure conditions | Artifacts |
|---|---|---|---|---|---|
| Dataset ingestion | Read source datasets | Excel/JSONL | Loaded records | missing/unreadable file | source data |
| Validation | Check quality/schema | loaded records | audit result | malformed/missing fields | audit report |
| Cleaning | Normalize data | raw records | cleaned data | structure/processing failure | cleaned output |
| PII handling | Detect/redact PII | cleaned records | de-identified records | PII processing failure | cleaned output |
| Deduplication | Remove duplicate records | cleaned records | deduplicated records | hash/processing failure | dedupe stats |
| Task formatting | Build training records | unified records | JSONL records | schema mismatch | train/val/test JSONL |
| Split | Build train/val/test | formatted records | 3 splits | invalid split input | split files |
| Fine-tuning | Train Qwen3 with LoRA | train JSONL + base model | adapter | CUDA OOM/config error | `ai/artifacts/full_training/` |
| Evaluation | Score held-out test | test JSONL + adapter | metrics | model/runtime failure | summary |
| Model validation | Apply readiness checks | evaluation result | readiness decision | quality/safety failure | report |
| Runtime registration | Make model selectable | model map + adapter | runtime catalog | missing adapter | service/registry |
| Inference | Answer requests | model/task/question/context | common response | load/generation failure | response metadata |
