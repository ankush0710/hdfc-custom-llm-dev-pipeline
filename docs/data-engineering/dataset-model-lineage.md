# Dataset / Model Lineage

## Summary of Lineage

* **Previous Dataset Release (Release A)**: 24,346 total (Train: 19,476 | Val: 2,434 | Test: 2,436).
* **Current Expanded Dataset (Release B)**: 59,346 total (Train: 47,476 | Val: 5,934 | Test: 5,936).
* **Dataset Used for Current Qwen3 Model**: Release A (19,476 training records).
* **Dataset Used for Current Evaluation**: Release A (2,436 test records).

## Formal Lineage Disclaimer

> "The current Qwen3 model was trained on the earlier dataset release; this 59,346-record dataset is a newer expanded release and has not been used to retrain the current model."

## Evidence

1. **Model Artifacts**: Checkpoint step count corresponds to 19,476 records over 3 epochs with batch size 16.
2. **Current Release Purpose**: Release B (59,346 records) is an expanded master corpus prepared for domain scaling, additional banking task types, and future model retraining cycles.
