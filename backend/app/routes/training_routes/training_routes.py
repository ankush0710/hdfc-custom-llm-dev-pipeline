from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.schema.training_schema.training_schema import (TrainingRunCreate, TrainingRunResponse)
from app.services.training_service.training_service import (create_training_run, get_training_runs, get_training_run_by_id, start_training_run)

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


@router.post(
    "/runs/{run_id}/start",
    response_model = TrainingRunResponse
)
def start_run(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    try:
        training_run = start_training_run(
            db=db,
            run_id=run_id,
            background_tasks=background_tasks,
        )

        if not training_run:
            raise HTTPException(
                status_code = 404,
                detail = "training not found"
            )

        return training_run

    except ValueError as error:
        raise HTTPException(
            status_code = 400,
            detail = str(error)
        )




@router.get(
    "/runs",
    response_model = list[TrainingRunResponse]
)
def get_all_runs(
    db: Session = Depends(get_db)
):

    return get_training_runs(db)


@router.get(
    "/runs/{run_id}",
    response_model = TrainingRunResponse
)
def get_run_by_id(
    run_id: int,
    db:Session = Depends(get_db)
):
    training_run = get_training_run_by_id(
        db,
        run_id
    )

    if not training_run:
        raise HTTPException(
            status_code=404,
            detail="Training run not found"
        )

    return training_run