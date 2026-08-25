from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dbConfig.database_config import get_db
from app.schema.evaluation_schema.evaluation_schema import (
    EvaluationCreate,
    EvaluationResponse,
)
import app.services.evaluation_service.evaluation_service as evaluation_service

router = APIRouter(
    prefix="/evaluations",
    tags=["Evaluations"]
)


# ======================== Create a new evaluation record =============================== #
@router.post(
    "/",
    response_model=EvaluationResponse
)
def create_evaluation(
    payload: EvaluationCreate,
    db: Session = Depends(get_db)
):
    try:
        return evaluation_service.create_evaluation(db, payload)
    except ValueError as error:
        err_msg = str(error)
        status_code = 404 if "not found" in err_msg.lower() else 400
        raise HTTPException(status_code=status_code, detail=err_msg)


# ======================== List all evaluations (optionally filter by run_id) =========== #
@router.get(
    "/",
    response_model=list[EvaluationResponse]
)
def list_evaluations(
    run_id: int | None = None,
    db: Session = Depends(get_db)
):
    return evaluation_service.list_evaluation(db, run_id)


# ======================== Get a single evaluation by id ================================ #
@router.get(
    "/{evaluation_id}",
    response_model=EvaluationResponse
)
def get_evaluation_by_id(
    evaluation_id: int,
    db: Session = Depends(get_db),
):
    evaluation = evaluation_service.get_evaluation_by_id(db, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


# ======================== Start evaluation (runs AI scoring in background) ============= #
@router.post(
    "/{evaluation_id}/start",
    response_model=EvaluationResponse
)
def start_evaluation(
    evaluation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        return evaluation_service.start_evaluation(
            db=db,
            evaluation_id=evaluation_id,
            background_tasks=background_tasks,
        )
    except ValueError as error:
        err_msg = str(error)
        status_code = 404 if "not found" in err_msg.lower() else 400
        raise HTTPException(status_code=status_code, detail=err_msg)