"""
MLflow retrospective run logger for the HDFC Custom LLM Development Pipeline.

This reconstructs previously completed training/evaluation evidence in MLflow.
It is intentionally labelled retrospective_tracking; it does not claim that
MLflow captured the original training run in real time.
"""
from __future__ import annotations

import os
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "mlflow.db"
EXPERIMENT_NAME = "HDFC-Custom-LLM"
RUN_NAME = "retrospective_qwen3_lora_release_a"


def _artifact(path: str) -> str:
    return str(PROJECT_ROOT / path)


def record_retrospective_run() -> str:
    mlflow.set_tracking_uri(f"sqlite:///{DB_PATH}")
    client = MlflowClient()

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = client.create_experiment(EXPERIMENT_NAME)
    else:
        experiment_id = experiment.experiment_id

    # Reuse an existing canonical run rather than creating duplicate runs.
    existing = client.search_runs(
        [experiment_id],
        filter_string="tags.canonical_run = 'true'",
        max_results=1,
    )
    if existing:
        print(f"Canonical retrospective run already exists: {existing[0].info.run_id}")
        return existing[0].info.run_id

    with mlflow.start_run(experiment_id=experiment_id, run_name=RUN_NAME) as run:
        mlflow.log_params({
            "base_model": "Qwen/Qwen3-0.6B",
            "training_method": "LoRA / PEFT",
            "adapter_path": "ai/artifacts/full_training/",
            "dataset_version": "Release A",
            "num_train_epochs": 1.0,
            "learning_rate": 0.0002,
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "max_seq_length": 256,
            "lora_r": 8,
            "lora_alpha": 16,
            "lora_dropout": 0.05,
            "seed": 42,
            "train_samples": 19476,
            "validation_samples": 2434,
            "test_samples": 2436,
            "total_dataset_samples": 24346,
            "gpu_hardware": "NVIDIA GeForce GTX 1650 Ti (4GB VRAM)",
        })

        mlflow.log_metrics({
            "train_loss": 0.42605914677009443,
            "global_steps": 2435,
            "train_runtime_seconds": 30406.9,
            "trainable_parameters": 2293760,
            "total_parameters": 598343680,
            "trainable_percentage": 0.3834,
            "peak_gpu_memory_mb": 2175,
            "eval_test_examples": 2436,
            "eval_intent_json_validity": 1.0,
            "eval_intent_structured_accuracy": 0.8290,
            "eval_answer_accuracy": 1.0,
            "eval_citation_accuracy": 0.0,
            "eval_policy_flag_accuracy": 1.0,
            "eval_escalation_accuracy": 1.0,
            "full_structured_match": 0.0,
            "normalized_exact_match": 0.2215,
            "eval_critical_safety_failures": 0,
            "eval_infrastructure_errors": 0,
            "eval_average_latency_sec": 3.83,
            "qa_tests_executed": 28,
            "qa_automated_pass": 27,
            "qa_automated_fail": 1,
            "qa_runtime_errors": 0,
            "qa_avg_latency_sec": 12.606,
        })

        mlflow.set_tags({
            "canonical_run": "true",
            "experiment_name": EXPERIMENT_NAME,
            "run_type": "retrospective_tracking",
            "tracking_status": "retrospective_reconstruction",
            "dataset_lineage": "Release A",
            "qa_sft_006_status": "FAIL_GROUNDEDNESS_DOC_436_MISSING",
            "evaluated_by": "Member 4 (QA) & Member 5 (MLOps)",
            "model_version": "v1.0.0-lora",
        })

        for relative, artifact_path in [
            ("ai_evidence/latest_evaluation_snapshot.json", "snapshots"),
            ("ai_evidence/training_snapshot.json", "snapshots"),
            ("dataset_evidence/data_manifest.json", "lineage"),
        ]:
            source = Path(_artifact(relative))
            if not source.is_file():
                raise FileNotFoundError(f"Required evidence file not found: {source}")
            mlflow.log_artifact(str(source), artifact_path=artifact_path)

        print(f"Retrospective run created successfully: {run.info.run_id}")
        return run.info.run_id


if __name__ == "__main__":
    record_retrospective_run()
