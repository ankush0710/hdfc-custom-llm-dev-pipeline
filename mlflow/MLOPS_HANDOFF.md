# MLOps Final Handoff

## Canonical run

- Experiment: `HDFC-Custom-LLM`
- Run name: `retrospective_qwen3_lora_release_a`
- Run ID: `256ef32b6b434eaf8d7db5d5df0aa32f`
- Status: `FINISHED`
- Tracking type: `retrospective_tracking`
- Tracking status: `retrospective_reconstruction`

## Model lineage

- Base model: `Qwen/Qwen3-0.6B`
- Fine-tuning: LoRA / PEFT
- Dataset: Release A
- Adapter: `ai/artifacts/full_training/`

## Evidence status

The bundled MLflow database was verified to contain exactly one active project run in `HDFC-Custom-LLM`. Earlier duplicate reconstruction attempts are marked deleted and are not canonical.

The canonical run records training parameters, training metrics, evaluation metrics, Member 4 QA metrics, lineage tags, and the relevant evidence artifacts.

## QA limitation

Member 4 reported 28 tests executed, 27 automated PASS, 1 automated FAIL, and 0 runtime errors. The failed case is SFT-006 (groundedness/citation integrity). Human semantic review remains required.

## Reproduction

From the package root:

```powershell
python mlflow/log_historical_run.py
```

The script resolves paths relative to the package root and reuses the existing canonical run instead of creating duplicates.

## Ownership

Member 5 is accountable for this MLOps/MLflow package. Member 6 is accountable for the project's general documentation and final presentation.
