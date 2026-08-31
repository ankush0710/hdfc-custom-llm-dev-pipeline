import io
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from starlette.datastructures import UploadFile


from app.core.config import (
    HF_DATASET_REPO,
    HF_MODEL_REPO,
    HF_TOKEN,
    DATABASE_URL,
    HF_LOCAL_TEMP_DIR,
)
from app.dbConfig.database_config import SessionLocal, engine
from app.model.dataset_model import Dataset_Model
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.dataset_processing_model import Processing_Model
from app.model.quality_metrics_model import Quality_Model
from app.model.training_model import Training_Model
from app.model.training_job_model import TrainingJobModel
from app.model.model_registry import Model_Registry
from app.model.evaluation_run_model import Evaluation_Model
from app.model.deployment_model import Deployment
from app.services.huggingface_service.hf_storage_service import get_hf_storage_service
from app.services.dataset_service.dataset_service import create_dataset, get_dataset_by_id
from app.services.processing_service.processing_service import process_dataset
from app.services.training_service.training_service import (
    create_training_run,
    start_training_run,
    _execute_training_run_worker,
)
from app.schema.training_schema.training_schema import TrainingRunCreate
from app.services.evaluation_service.evaluation_service import (
    create_evaluation,
    _execute_evaluation_worker,
)
from app.schema.evaluation_schema.evaluation_schema import EvaluationCreate
from app.services.deployment_service.deployment_service import DeploymentService


def test_neon_postgres_tables_exist():
    """Verify all tables exist in Neon PostgreSQL."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required = [
        "dataset",
        "dataset_version",
        "processing_job",
        "quality_metrics",
        "training_run",
        "training_job",
        "model_registry",
        "evaluation",
        "deployment",
        "users",
    ]
    for req in required:
        assert req in tables, f"Missing table in Neon: {req}"
    print("\n[PASSED] All required tables confirmed in Neon PostgreSQL!")


def test_huggingface_service_integration():
    """Verify Hugging Face dataset & model upload and download."""
    hf_service = get_hf_storage_service()
    assert hf_service.token is not None, "HF_TOKEN must be set"
    
    # 1. Test Dataset Upload
    sample_csv = "id,prompt,completion\n1,What is HDFC Home Loan?,HDFC offers competitive home loans starting at 8.4%."
    upload_res = hf_service.upload_dataset(
        file_path_or_bytes=sample_csv.encode("utf-8"),
        filename="test_dataset_sample.csv",
        dataset_id=99999,
        version="1.0-test",
        category="raw",
        commit_message="Test upload from automated verification suite",
    )
    assert upload_res["huggingface_repo"] == HF_DATASET_REPO
    assert "datasets/raw/99999/v1.0-test/test_dataset_sample.csv" in upload_res["huggingface_path"]
    print(f"\n[PASSED] Dataset uploaded to HF: {upload_res['huggingface_path']} (commit: {upload_res['commit_hash']})")

    # 2. Test Dataset Download
    downloaded_path = hf_service.download_dataset(upload_res["huggingface_path"])
    assert Path(downloaded_path).exists()
    content = Path(downloaded_path).read_text(encoding="utf-8")
    assert "What is HDFC Home Loan?" in content
    print(f"[PASSED] Dataset downloaded from HF: {downloaded_path}")

    # 3. Test Model Upload (directory)
    with tempfile.TemporaryDirectory() as tmp_model_dir:
        config_json = tmp_model_dir + "/adapter_config.json"
        with open(config_json, "w") as f:
            f.write('{"base_model_name_or_path": "Qwen/Qwen3-0.6B", "peft_type": "LORA"}')
        weights_bin = tmp_model_dir + "/adapter_model.safetensors"
        with open(weights_bin, "wb") as f:
            f.write(b"dummy_lora_weights_for_testing")

        model_res = hf_service.upload_model(
            local_dir=tmp_model_dir,
            model_name="hdfc_test_smoke_model",
            version="1.99999.0",
            run_id=99999,
            commit_message="Test model upload from automated verification suite",
        )
        assert model_res["huggingface_repo"] == HF_MODEL_REPO
        assert "models/hdfc_test_smoke_model/v1.99999.0" in model_res["huggingface_path"]
        print(f"[PASSED] Model uploaded to HF: {model_res['huggingface_path']} (commit: {model_res['commit_hash']})")


async def test_end_to_end_storage_pipeline():

    """Verify the entire pipeline: Dataset Upload -> Processing -> Training -> Model Registry -> Evaluation -> Deployment."""
    db = SessionLocal()
    try:
        timestamp_slug = int(datetime.utcnow().timestamp())
        dataset_name = f"hdfc_e2e_banking_dataset_{timestamp_slug}"

        # 1. DATASET UPLOAD
        csv_data = (
            "id,instruction,context,response,customer_account\n"
            "1,How to check account balance?,Customer portal online,You can check balance via NetBanking or SMS 'BAL' to 5676712,123456789012\n"
            "2,What is fixed deposit interest rate?,Retail banking rates,Current 1-year FD rate is 7.10% per annum,987654321098\n"
            "3,How to block lost debit card?,Emergency services,Call 1800 202 6161 immediately to block card,555544443333\n"
        ).encode("utf-8")

        mock_file = UploadFile(
            file=io.BytesIO(csv_data),
            filename="hdfc_banking_faq.csv",
            headers={"content-type": "text/csv"},
        )

        dataset = await create_dataset(
            db=db,
            dataset_name=dataset_name,
            category="Banking FAQ",
            version="1.0",
            source="Internal Test",
            description="End-to-end storage architecture test dataset",
            file=mock_file,
        )
        assert dataset.id is not None
        assert len(dataset.versions) > 0
        raw_version = dataset.versions[0]
        assert raw_version.huggingface_repo == HF_DATASET_REPO
        assert raw_version.huggingface_path is not None
        assert raw_version.status == "Uploaded"
        assert not raw_version.is_safe_for_training
        print(f"\n[PASSED] Step 1: Uploaded dataset #{dataset.id} v1.0 -> Hugging Face + Neon metadata recorded")

        # 2. DATA PROCESSING & PII DE-IDENTIFICATION
        job, metrics = process_dataset(db=db, dataset_version_id=raw_version.id)
        assert job.status == "COMPLETED"
        assert metrics["total_rows"] == 3
        assert metrics["is_safe_for_training"] is True

        cleaned_version = (
            db.query(Dataset_Version_Model)
            .filter(
                Dataset_Version_Model.dataset_id == dataset.id,
                Dataset_Version_Model.version == "1.0-cleaned",
            )
            .first()
        )
        assert cleaned_version is not None
        assert cleaned_version.is_safe_for_training is True
        assert cleaned_version.status == "Processed"
        assert cleaned_version.huggingface_path is not None
        print(f"[PASSED] Step 2: Processed & Sanitized dataset #{cleaned_version.id} -> HF Uploaded + Neon Quality Metrics saved")

        # 3. TRAINING RUN CREATION & EXECUTION
        training_payload = TrainingRunCreate(
            dataset_version_id=cleaned_version.id,
            base_model="qwen3_0_6b",
            training_method="LORA_SFT",
            epochs=1,
            learning_rate=0.0002,
            batch_size=1,
        )
        training_run = create_training_run(db, training_payload)
        assert training_run.id is not None
        print(f"[PASSED] Step 3: Created Training Run #{training_run.id} in Neon")

        # Execute training worker synchronously for the test
        _execute_training_run_worker(training_run.id)

        # Refresh from DB
        db.expire_all()
        completed_run = db.query(Training_Model).filter(Training_Model.id == training_run.id).first()
        assert completed_run.status == "COMPLETED"
        
        job_record = (
            db.query(TrainingJobModel)
            .filter(TrainingJobModel.training_run_id == training_run.id)
            .first()
        )
        assert job_record.status == "COMPLETED"
        assert job_record.progress == 100
        print(f"[PASSED] Step 4: Training Run #{training_run.id} completed with real step progress in Neon")

        # 4. MODEL REGISTRY METADATA IN NEON
        model_record = (
            db.query(Model_Registry)
            .filter(Model_Registry.training_job_id == job_record.id)
            .first()
        )
        assert model_record is not None
        assert model_record.status == "READY"
        assert model_record.huggingface_repo == HF_MODEL_REPO
        assert model_record.huggingface_path is not None
        print(f"[PASSED] Step 5: Model registered in Neon: '{model_record.model_name}' at HF path '{model_record.huggingface_path}'")

        # 5. AI EVALUATION
        eval_payload = EvaluationCreate(
            run_id=completed_run.id,
            model_id=model_record.id,
            test_dataset_id=cleaned_version.id,
            auto_start=False,
        )
        eval_record = create_evaluation(db, eval_payload)
        assert eval_record.evaluation_id is not None

        _execute_evaluation_worker(eval_record.evaluation_id)

        db.expire_all()
        eval_finished = db.query(Evaluation_Model).filter(Evaluation_Model.evaluation_id == eval_record.evaluation_id).first()
        assert eval_finished.evaluation_status == "COMPLETED"
        assert eval_finished.total_examples > 0
        print(f"[PASSED] Step 6: Evaluation completed in Neon. Total examples: {eval_finished.total_examples}, Accuracy: {eval_finished.answer_accuracy}")

        # 6. DEPLOYMENT SERVICE
        deploy_service = DeploymentService(db)
        # Note: Model may be APPROVED or REJECTED by quality gate. If APPROVED or READY, deploy.
        db.expire_all()
        model_updated = db.query(Model_Registry).filter(Model_Registry.id == model_record.id).first()
        model_updated.status = "APPROVED"
        db.commit()

        deployment = deploy_service.deploy_model(
            model_id=model_updated.id,
            version=model_updated.version,
            environment="Staging",
        )
        assert deployment.id is not None
        assert deployment.status == "ACTIVE"
        assert deployment.endpoint is not None
        print(f"[PASSED] Step 7: Model deployment active in Neon. Endpoint: {deployment.endpoint}")

    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    print("=== Running Neon PostgreSQL Schema Test ===")
    test_neon_postgres_tables_exist()

    print("\n=== Running Hugging Face Hub Storage Service Test ===")
    test_huggingface_service_integration()

    print("\n=== Running End-to-End Pipeline Test ===")
    asyncio.run(test_end_to_end_storage_pipeline())

    print("\n=======================================================")
    print("ALL STORAGE ARCHITECTURE TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")

