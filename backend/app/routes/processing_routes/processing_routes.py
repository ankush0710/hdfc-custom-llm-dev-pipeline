# ================================================================================ #
# Processing routes -> 
# ================================================================================ #

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.schema.dataset_processing_schema import (ProcessingRequest, ProcessingResponse, ProcessingStatusResponse)
from app.model.dataset_processing_model import Processing_Model
from app.services.processing_service.processing_service import process_dataset

router = APIRouter(
    prefix="/data-processing",
    tags=["Data Processing"]
)

@router.post("/jobs", response_model=ProcessingResponse)
async def start_processing(
    request: ProcessingRequest,
    db: Session = Depends(get_db)
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
            "status": job.status
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
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
    job_id:int,
    db:Session = Depends(get_db)
):
    job = (db.query(Processing_Model).filter(Processing_Model.id == job_id).first())

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found"
        )

    return{
        "job_id":job.id,
        "dataset_version_id":job.dataset_version_id,
        "status":job.status,
        "output_file":job.output_file,
        "error_message":job.error_message
    }


@router.get("/jobs/{job_id}/metrics")
def get_job_quality_metrics(
    job_id: int,
    db: Session = Depends(get_db)
):
    from app.services.processing_service.processing_service import get_processing_metrics
    metrics = get_processing_metrics(db, job_id)

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail="Quality metrics not found for this job"
        )

    return {
        "job_id": metrics.job_id,
        "total_rows": metrics.total_rows,
        "total_columns": metrics.total_columns,
        "duplicate_rows": metrics.duplicate_rows,
        "missing_values": metrics.missing_values,
        "empty_rows": metrics.empty_rows,
        "quality_score": metrics.quality_score
    }
    



