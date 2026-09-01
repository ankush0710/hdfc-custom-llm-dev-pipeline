# MLflow MLOps Handoff

## Purpose

This package provides the MLOps/MLflow evidence for the HDFC Custom LLM Development Pipeline.

The original Qwen3 training and evaluation completed before this MLflow package was created. Therefore, the MLflow record is a **retrospective reconstruction** of verified historical evidence. It must not be described as live training-time tracking.

## Canonical MLflow experiment

```text
HDFC-Custom-LLM
```

## Canonical retrospective run

```text
Run name: retrospective_qwen3_lora_release_a
Run ID: 256ef32b6b434eaf8d7db5d5df0aa32f
Status: FINISHED
Tracking type: retrospective_tracking
Tracking status: retrospective_reconstruction
```

The bundled `mlflow.db` has one active project run in this experiment. Earlier duplicate reconstruction attempts are retained only as deleted historical records; they are not canonical.

## Model and lineage

```text
Base model:       Qwen/Qwen3-0.6B
Training method:  LoRA / PEFT
Dataset release:  Release A
Adapter:          ai/artifacts/full_training/
```

Release A contains 19,476 training records, 2,434 validation records, and 2,436 test records (24,346 total).

The later `v2.0.0-expanded` dataset is a separate release and was not used to train the current Qwen3 adapter.

## Training parameters

| Parameter | Value |
|---|---:|
| Epochs | 1.0 |
| Learning rate | 0.0002 |
| Per-device train batch size | 1 |
| Gradient accumulation steps | 8 |
| Maximum sequence length | 256 |
| LoRA rank | 8 |
| LoRA alpha | 16 |
| LoRA dropout | 0.05 |
| Seed | 42 |

## Training metrics

| Metric | Value |
|---|---:|
| Train loss | 0.4260591468 |
| Global steps | 2,435 |
| Training runtime (s) | 30,406.9 |
| Trainable parameters | 2,293,760 |
| Total parameters | 598,343,680 |
| Trainable percentage | 0.3834% |
| Peak GPU memory (MB) | ~2,175 |

## Evaluation metrics

| Metric | Value |
|---|---:|
| Test examples | 2,436 |
| Intent JSON validity | 1.0000 |
| Intent structured accuracy | 0.8290 |
| Answer accuracy | 1.0000 |
| Citation accuracy | 0.0000 |
| Policy flag accuracy | 1.0000 |
| Escalation accuracy | 1.0000 |
| Full structured match | 0.0000 |
| Normalized exact match | 0.2215 |
| Critical safety failures | 0 |
| Infrastructure errors | 0 |
| Average latency (s) | ~3.83 |

## Member 4 QA

```text
Tests executed: 28
Automated PASS: 27
Automated FAIL: 1
Runtime errors: 0
Average latency: 12.606 s
```

The failing test is `SFT-006`, a groundedness/citation-integrity finding. The generated citation `HDFC Master Policy Doc #436` was not supported by the supplied fixture context. Human semantic review remains required.

## Logged artifacts

The canonical run contains verified copies of:

- `ai_evidence/training_snapshot.json`
- `ai_evidence/latest_evaluation_snapshot.json`
- `dataset_evidence/data_manifest.json`

Large raw datasets are intentionally not copied into MLflow.

## Reproducibility

The logger is path-independent and resolves evidence relative to the package root. From the package root, run:

```powershell
python mlflow/log_historical_run.py
```

If the canonical run already exists, the script reports its Run ID rather than creating another duplicate.

### Portable MLflow evidence viewer

The bundled SQLite database is an evidence snapshot and its historical local artifact URIs were originally recorded as Windows filesystem paths. To make the package portable after extraction, do **not** launch MLflow with a copied absolute URI. Start it through the included launcher instead:

```powershell
python mlflow/start_portable.py
```

The launcher detects the current package directory, rebinds local run artifact URIs to the bundled `mlruns/` directory, and starts a single-worker local MLflow server. This avoids machine-specific `C:\Download\...` paths and is the supported way to view the packaged evidence from a new extraction directory.

The database is still a local evidence snapshot, not a shared production MLflow service.

## Team ownership

Member 5 owns MLOps/MLflow only. Member 6 owns the final project documentation and presentation. Backend/frontend/deployment implementation remains with Member 3; AI/ML remains with Member 1; data engineering remains with Member 2; evaluation/QA remains with Member 4.

## Security

Do not include `.env` files, tokens, passwords, private keys, or other secrets in this package or repository.

### Portability note

This is a local MLflow evidence snapshot, not a production tracking server. Run `python mlflow/start_portable.py` from the extracted package root. The launcher rebinds local artifact URIs to the current extraction path. Historical/deleted runs may remain in the SQLite database without bundled artifact payloads; these are skipped and do not block startup.
