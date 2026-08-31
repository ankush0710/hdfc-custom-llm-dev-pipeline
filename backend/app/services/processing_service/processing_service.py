import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

# import all required models 
from app.model.dataset_processing_model import Processing_Model
from app.model.quality_metrics_model import Quality_Model
from app.model.dataset_version_model import Dataset_Version_Model

# import all processors methods
from app.processor.cleaner import clean_file
from app.processor.validator import load_file, resolve_file_path
from app.processor.calculate_quality_metrics import calculate_quality_metrics
from app.processor.deDuplicator import remove_duplicate
from app.processor.pii_detector import deidentify_dataframe, verify_pii_safe
from app.utils.file_utils import create_processed_path
from app.services.huggingface_service.hf_storage_service import get_hf_storage_service
from app.core.config import HF_LOCAL_TEMP_DIR


def process_dataset(db: Session, dataset_version_id: int, operations: list[str] = None):
    if operations is None or not operations:
        operations = ["clean", "remove_duplicate", "detect_pii", "deidentify_pii"]

    dataset_version = (
        db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == dataset_version_id).first()
    )

    if not dataset_version:
        raise ValueError("Dataset version not found")

    hf_service = get_hf_storage_service()
    temp_input_downloaded = False
    input_file = None

    # Resolve local path or download from Hugging Face
    raw_path = dataset_version.file_path or dataset_version.huggingface_path
    if raw_path and os.path.exists(raw_path):
        input_file = raw_path
    elif dataset_version.huggingface_path:
        input_file = str(hf_service.download_dataset(dataset_version.huggingface_path))
        temp_input_downloaded = True
    else:
        input_file = resolve_file_path(raw_path)

    if not input_file or not os.path.exists(input_file):
        raise FileNotFoundError(f"Could not locate dataset version file on server or Hugging Face ({raw_path})")

    job = Processing_Model(
        dataset_version_id=dataset_version_id,
        status="RUNNING",
        input_file=dataset_version.huggingface_path or dataset_version.file_path or input_file,
        started_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    temp_output_file = None

    try:
        # =========================== #
        # 1. LOAD DATASET
        # =========================== #
        df = load_file(input_file)
        duplicate_count = 0

        # =========================== #
        # 2. CLEAN DATASET (UTF-8 & Formatting)
        # =========================== #
        if "clean" in operations or any("clean" in op.lower() for op in operations):
            df = clean_file(df)

        # =========================== #
        # 3. REMOVE DUPLICATES
        # =========================== #
        if "remove_duplicate" in operations or any("duplicate" in op.lower() for op in operations):
            df, duplicate_count = remove_duplicate(df)

        # =========================== #
        # 4. PII & SENSITIVE BANKING DATA DETECTION & REDACTION
        # =========================== #
        pii_summary = {
            "pii_instances_detected": 0,
            "pii_types_detected": "NONE",
            "records_sanitized": 0,
            "is_safe_for_training": True,
            "pii_scan_status": "PASSED"
        }

        should_run_pii = (
            "detect_pii" in operations or 
            "deidentify_pii" in operations or 
            "pii" in operations or 
            True # Always enforce security scan in banking LLM pipeline
        )

        if should_run_pii:
            df, pii_summary = deidentify_dataframe(df)

            # Verification gate: ensure 0 residual sensitive data items remain
            is_safe, violations = verify_pii_safe(df)
            if not is_safe:
                pii_summary["is_safe_for_training"] = False
                pii_summary["pii_scan_status"] = "FAILED"
                raise ValueError(f"PII Verification Gate Failed: Residual sensitive data detected ({violations[:3]})")
            else:
                pii_summary["is_safe_for_training"] = True
                pii_summary["pii_scan_status"] = "PASSED"

        # =========================== #
        # 5. CHECK QUALITY METRICS
        # =========================== #
        metrics = calculate_quality_metrics(df, duplicate_rows=duplicate_count)
        metrics.update(pii_summary)

        # =========================== #
        # 6. SAVE PROCESSED DATA TEMPORARILY
        # =========================== #
        temp_proc_dir = Path(HF_LOCAL_TEMP_DIR) / "processing" / f"job_{job.id}"
        temp_proc_dir.mkdir(parents=True, exist_ok=True)
        
        orig_ext = Path(input_file).suffix.lower() or ".csv"
        clean_filename = f"processed_{Path(dataset_version.file_name).stem}{orig_ext}"
        temp_output_file = str(temp_proc_dir / clean_filename)

        if orig_ext == ".csv":
            df.to_csv(temp_output_file, index=False)
        elif orig_ext == ".xlsx":
            df.to_excel(temp_output_file, index=False)
        elif orig_ext == ".json":
            df.to_json(temp_output_file, orient="records")
        elif orig_ext == ".jsonl":
            df.to_json(temp_output_file, orient="records", lines=True)
        else:
            df.to_csv(temp_output_file, index=False)

        # =========================== #
        # 7. UPLOAD PROCESSED DATASET TO HUGGING FACE
        # =========================== #
        cleaned_version_name = f"{dataset_version.version}-cleaned"
        with open(temp_output_file, "rb") as f:
            proc_bytes = f.read()
        proc_hash = hashlib.sha256(proc_bytes).hexdigest()
        file_size_mb = len(proc_bytes) / (1024 * 1024)

        hf_upload = hf_service.upload_dataset(
            file_path_or_bytes=proc_bytes,
            filename=clean_filename,
            dataset_id=dataset_version.dataset_id,
            version=cleaned_version_name,
            category="processed",
            commit_message=f"Upload sanitized processed dataset #{dataset_version.dataset_id} v{cleaned_version_name}",
        )

        # =========================== #
        # 8. UPDATE PROCESSING JOB METADATA IN NEON
        # =========================== #
        job.status = "COMPLETED"
        job.output_file = hf_upload["huggingface_path"]
        job.completed_at = datetime.utcnow()

        # =========================== #
        # 9. LINEAGE & SAFETY PROTECTION
        # =========================== #
        dataset_version.status = "Uploaded"
        dataset_version.is_safe_for_training = False
        dataset_version.pii_scan_status = "SCANNED"

        # ============================ #
        # 10. SAVE QUALITY & PII METRICS IN NEON
        # ============================ #
        quality = Quality_Model(
            job_id=job.id,
            total_rows=metrics["total_rows"],
            total_columns=metrics["total_columns"],
            duplicate_rows=metrics["duplicate_rows"],
            missing_values=metrics["missing_values"],
            empty_rows=metrics["empty_rows"],
            quality_score=metrics["quality_score"],
            pii_instances_detected=metrics["pii_instances_detected"],
            pii_types_detected=metrics["pii_types_detected"],
            records_sanitized=metrics["records_sanitized"],
            is_safe_for_training=metrics["is_safe_for_training"],
        )
        db.add(quality)

        # ============================ #
        # 11. REGISTER SANITIZED PROCESSED DATASET VERSION IN NEON
        # ============================ #
        existing_version = (
            db.query(Dataset_Version_Model)
            .filter(
                Dataset_Version_Model.dataset_id == dataset_version.dataset_id,
                Dataset_Version_Model.version == cleaned_version_name
            )
            .first()
        )

        if not existing_version:
            cleaned_version = Dataset_Version_Model(
                dataset_id=dataset_version.dataset_id,
                version=cleaned_version_name,
                file_name=clean_filename,
                file_path=hf_upload["huggingface_path"],
                file_size=file_size_mb,
                file_type=orig_ext.replace(".", "").upper(),
                file_hash=proc_hash,
                status="Processed",
                is_safe_for_training=True,
                pii_scan_status="PASSED",
                huggingface_repo=hf_upload["huggingface_repo"],
                huggingface_path=hf_upload["huggingface_path"],
                commit_hash=hf_upload["commit_hash"],
            )
            db.add(cleaned_version)
        else:
            existing_version.file_path = hf_upload["huggingface_path"]
            existing_version.file_size = file_size_mb
            existing_version.file_hash = proc_hash
            existing_version.status = "Processed"
            existing_version.is_safe_for_training = True
            existing_version.pii_scan_status = "PASSED"
            existing_version.huggingface_repo = hf_upload["huggingface_repo"]
            existing_version.huggingface_path = hf_upload["huggingface_path"]
            existing_version.commit_hash = hf_upload["commit_hash"]

        db.commit()

        # ============================ #
        # 12. CLEAN UP TEMPORARY LOCAL FILES
        # ============================ #
        if temp_output_file and os.path.exists(temp_output_file):
            shutil.rmtree(temp_proc_dir, ignore_errors=True)
        if temp_input_downloaded and os.path.exists(input_file):
            try:
                os.remove(input_file)
            except Exception:
                pass

        return job, metrics

    except Exception as error:
        job.status = "FAILED"
        job.error_message = str(error)
        job.completed_at = datetime.utcnow()
        db.commit()
        if temp_output_file and os.path.exists(temp_output_file):
            shutil.rmtree(Path(temp_output_file).parent, ignore_errors=True)
        raise error



def get_processing_metrics(db: Session, job_id: int):
    return db.query(Quality_Model).filter(Quality_Model.job_id == job_id).first()




        

