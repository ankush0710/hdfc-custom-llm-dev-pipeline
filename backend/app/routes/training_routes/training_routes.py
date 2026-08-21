from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.schema.training_schema.training_schema import (TrainingRunCreate, TrainingRunResponse)
from app.services.training_service.training_service import create_training_run

router = APIRouter(
    prefix="/training",
    tags=["Training"]
)

@router.post(
    "/runs",
    response_model = TrainingRunResponse
)
def create_run(
    data: TrainingRunCreate,
    db: Session = Depends(get_db)
):

    return create_training_run(db, data)


