from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db

from app.schema.training_job_schema.training_job_schema import (
    TrainingJobCreate,
    TrainingJobResponse
)

from app.services.training_job_service.training_job_service import (
    create_training_job,
    get_training_jobs,
    get_training_job_by_id
)


router = APIRouter(
    prefix="/training-jobs",
    tags=["Training Jobs"]
)


@router.post(
    "",
    response_model=TrainingJobResponse
)
def create_job(
    data: TrainingJobCreate,
    db: Session = Depends(get_db)
):

    job = create_training_job(
        db,
        data.training_run_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Training run not found"
        )

    return job


@router.get(
    "",
    response_model=list[TrainingJobResponse]
)
def get_jobs(
    db: Session = Depends(get_db)
):

    return get_training_jobs(db)


@router.get(
    "/{job_id}",
    response_model=TrainingJobResponse
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = get_training_job_by_id(
        db,
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Training job not found"
        )

    return job