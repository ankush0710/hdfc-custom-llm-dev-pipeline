from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.dbConfig.database_config import get_db
from app.model.user_model import User_Model
from app.schema.training_job_schema.training_job_schema import (
    TrainingJobResponse
)

from app.services.training_job_service.training_job_service import (
    get_training_jobs,
    get_training_job_by_id
)


router = APIRouter(
    prefix="/training-jobs",
    tags=["Training Jobs"]
)


# Read-only: list all training jobs (auto-created when a training run starts)
@router.get(
    "",
    response_model=list[TrainingJobResponse]
)
def get_jobs(
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    return get_training_jobs(db)


# Read-only: get a specific training job by id
@router.get(
    "/{job_id}",
    response_model=TrainingJobResponse
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(get_current_user),
):
    job = get_training_job_by_id(db, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Training job not found"
        )

    return job