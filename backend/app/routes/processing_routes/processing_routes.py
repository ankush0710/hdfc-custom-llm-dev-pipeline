# ================================================================================ #
# Processing routes -> 
# ================================================================================ #

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth_dependency import get_current_user, require_permission, require_roles
from app.dbConfig.database_config import get_db
from app.model.dataset_processing_model import Processing_Model
from app.model.user_model import User_Model
from app.schema.dataset_processing_schema import (ProcessingRequest, ProcessingResponse, ProcessingStatusResponse)
from app.services.processing_service.processing_service import process_dataset

router = APIRouter(
    prefix="/data-processing",
    tags=["Data Processing"]
)

@router.post("/jobs", response_model=ProcessingResponse)
async def start_processing(
    request: ProcessingRequest,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("dataset:process")),
):
    try:
        job, metrics = process_dataset(
            db=db,
            dataset_version_id=request.dataset_version_id,
            operations=request.operations
        )

        return {
            "job_id": job.id,
            "dataset_version_id": job.dataset_version_id,
            "status": job.status,
            "pii_instances_detected": metrics.get("pii_instances_detected", 0),
            "pii_types_detected": metrics.get("pii_types_detected", "NONE"),
            "records_sanitized": metrics.get("records_sanitized", 0),
            "is_safe_for_training": metrics.get("is_safe_for_training", False),
        }

    except ValueError as error:
        status_code = 404 if "not found" in str(error).lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

#  route for getting the metrics as a result 
@router.get("/jobs/{job_id}", response_model=ProcessingStatusResponse)
def get_processing_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("dataset:read")),
):
    job = (db.query(Processing_Model).filter(Processing_Model.id == job_id).first())

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found"
        )

    quality = job.quality_metrics
    pii_instances = quality.pii_instances_detected if quality else 0
    pii_types = quality.pii_types_detected if quality else "NONE"
    records_sanitized = quality.records_sanitized if quality else 0
    is_safe = quality.is_safe_for_training if quality else (job.status == "COMPLETED")

    return {
        "job_id": job.id,
        "dataset_version_id": job.dataset_version_id,
        "status": job.status,
        "output_file": job.output_file,
        "error_message": job.error_message,
        "pii_instances_detected": pii_instances,
        "pii_types_detected": pii_types,
        "records_sanitized": records_sanitized,
        "is_safe_for_training": is_safe,
    }


from app.model.dataset_version_model import Dataset_Version_Model
from app.processor.validator import load_file, resolve_file_path
from app.processor.calculate_quality_metrics import calculate_quality_metrics
import os


@router.get("/versions/{version_id}/metrics")
def get_version_quality_metrics(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("dataset:read")),
):
    version = db.query(Dataset_Version_Model).filter(Dataset_Version_Model.id == version_id).first()
    if not version:
        return None

    # 1. Check if a completed processing job exists for this version (as input or output)
    job = (
        db.query(Processing_Model)
        .filter(Processing_Model.dataset_version_id == version_id)
        .order_by(Processing_Model.id.desc())
        .first()
    )
    if job:
        from app.services.processing_service.processing_service import get_processing_metrics
        metrics = get_processing_metrics(db, job.id)
        if metrics:
            return {
                "job_id": metrics.job_id,
                "total_rows": metrics.total_rows,
                "total_records": metrics.total_rows,
                "record_count": metrics.total_rows,
                "total_columns": metrics.total_columns,
                "column_count": metrics.total_columns,
                "duplicate_rows": metrics.duplicate_rows,
                "missing_values": metrics.missing_values,
                "empty_rows": metrics.empty_rows,
                "quality_score": metrics.quality_score,
                "qualityScore": metrics.quality_score,
                "pii_instances_detected": metrics.pii_instances_detected,
                "pii_types_detected": metrics.pii_types_detected,
                "records_sanitized": metrics.records_sanitized,
                "is_safe_for_training": metrics.is_safe_for_training,
                "pii_scan_status": version.pii_scan_status,
            }

    # 2. Check if this version was produced by another version's processing job
    parent_job = (
        db.query(Processing_Model)
        .filter(Processing_Model.output_file == version.file_path)
        .order_by(Processing_Model.id.desc())
        .first()
    )
    if parent_job:
        from app.services.processing_service.processing_service import get_processing_metrics
        metrics = get_processing_metrics(db, parent_job.id)
        if metrics:
            return {
                "job_id": metrics.job_id,
                "total_rows": metrics.total_rows,
                "total_records": metrics.total_rows,
                "record_count": metrics.total_rows,
                "total_columns": metrics.total_columns,
                "column_count": metrics.total_columns,
                "duplicate_rows": metrics.duplicate_rows,
                "missing_values": metrics.missing_values,
                "empty_rows": metrics.empty_rows,
                "quality_score": metrics.quality_score,
                "qualityScore": metrics.quality_score,
                "pii_instances_detected": metrics.pii_instances_detected,
                "pii_types_detected": metrics.pii_types_detected,
                "records_sanitized": metrics.records_sanitized,
                "is_safe_for_training": metrics.is_safe_for_training,
                "pii_scan_status": version.pii_scan_status,
            }

    # 3. Calculate statistics directly from the physical file on disk or Hugging Face
    try:
        target_path = version.file_path or version.huggingface_path
        if target_path:
            resolved_p = None
            if os.path.exists(target_path):
                resolved_p = target_path
            elif version.huggingface_path:
                from app.services.huggingface_service.hf_storage_service import get_hf_storage_service
                try:
                    resolved_p = str(get_hf_storage_service().download_dataset(version.huggingface_path))
                except Exception:
                    resolved_p = resolve_file_path(target_path)
            else:
                resolved_p = resolve_file_path(target_path)

            if resolved_p and os.path.exists(resolved_p):
                df = load_file(resolved_p)
                stats = calculate_quality_metrics(df)
                return {
                    "job_id": None,
                    "total_rows": stats["total_rows"],
                    "total_records": stats["total_rows"],
                    "record_count": stats["total_rows"],
                    "total_columns": stats["total_columns"],
                    "column_count": stats["total_columns"],
                    "duplicate_rows": stats.get("duplicate_rows", 0),
                    "missing_values": stats.get("missing_values", 0),
                    "empty_rows": stats.get("empty_rows", 0),
                    "quality_score": stats.get("quality_score", 100.0),
                    "qualityScore": stats.get("quality_score", 100.0),
                    "pii_instances_detected": 0,
                    "pii_types_detected": "NONE",
                    "records_sanitized": 0,
                    "is_safe_for_training": version.is_safe_for_training,
                    "pii_scan_status": version.pii_scan_status,
                }
    except Exception:
        pass

    return None

