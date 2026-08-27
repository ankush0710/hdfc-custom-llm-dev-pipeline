# import required default libraries
import os
from datetime import datetime
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

def process_dataset(db: Session, dataset_version_id: int, operations: list[str] = None):
    if operations is None or not operations:
        operations = ["clean", "remove_duplicate", "detect_pii", "deidentify_pii"]

    dataset_version = (
        db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == dataset_version_id).first()
    )

    if not dataset_version:
        raise ValueError("Dataset version not found")
    
    input_file = resolve_file_path(dataset_version.file_path)

    job = Processing_Model(
        dataset_version_id=dataset_version_id,
        status="Running",
        input_file=input_file,
        started_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

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
        # By default or if requested, always de-identify sensitive data
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
                # Re-verify and log
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
        # 6. SAVE PROCESSED DATA
        # =========================== #
        output_file = create_processed_path(
            dataset_version_id,
            input_file
        )

        extension = os.path.splitext(output_file)[1].lower()

        if extension == ".csv":
            df.to_csv(output_file, index=False)
        elif extension == ".xlsx":
            df.to_excel(output_file, index=False)
        elif extension == ".json":
            df.to_json(output_file, orient="records")
        elif extension == ".jsonl":
            df.to_json(output_file, orient="records", lines=True)

        # =========================== #
        # 7. UPDATE PROCESSING JOB
        # =========================== #
        job.status = "COMPLETED"
        job.output_file = output_file
        job.completed_at = datetime.utcnow()

        # =========================== #
        # 8. LINEAGE & SAFETY PROTECTION
        # Raw uploaded version retains 'Uploaded' status and is marked NOT safe for training
        # to prevent raw datasets from ever entering training pipeline.
        # =========================== #
        is_already_processed_file = "storage/processed" in input_file.replace("\\", "/") or "cleaned" in dataset_version.version.lower()
        if not is_already_processed_file:
            dataset_version.status = "Uploaded"
            dataset_version.is_safe_for_training = False
            dataset_version.pii_scan_status = "SCANNED"

        # ============================ #
        # 9. SAVE QUALITY & PII METRICS
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
        # 10. REGISTER SANITIZED PROCESSED DATASET VERSION
        # ============================ #
        cleaned_version_name = f"{dataset_version.version}-cleaned"
        existing_version = (
            db.query(Dataset_Version_Model)
            .filter(
                Dataset_Version_Model.dataset_id == dataset_version.dataset_id,
                Dataset_Version_Model.version == cleaned_version_name
            )
            .first()
        )

        if not existing_version and os.path.exists(output_file):
            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            cleaned_version = Dataset_Version_Model(
                dataset_id=dataset_version.dataset_id,
                version=cleaned_version_name,
                file_name=os.path.basename(output_file),
                file_path=output_file,
                file_size=file_size_mb,
                file_type=extension.replace(".", "").upper(),
                status="Processed",
                is_safe_for_training=True,
                pii_scan_status="PASSED"
            )
            db.add(cleaned_version)
        elif existing_version:
            # Update existing cleaned version with new output file and pass status
            existing_version.file_path = output_file
            existing_version.file_size = os.path.getsize(output_file) / (1024 * 1024)
            existing_version.status = "Processed"
            existing_version.is_safe_for_training = True
            existing_version.pii_scan_status = "PASSED"

        db.commit()

        return job, metrics

    except Exception as error:
        job.status = "FAILED"
        job.error_message = str(error)
        job.completed_at = datetime.utcnow()
        db.commit()
        raise error


def get_processing_metrics(db: Session, job_id: int):
    return db.query(Quality_Model).filter(Quality_Model.job_id == job_id).first()




        

