from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dbConfig.database_config import get_db
from app.schema.evaluation_schema.evaluation_schema import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationResult,
)
import app.services.evaluation_service.evaluation_service as evaluation_service

router = APIRouter(
    prefix="/evaluations",
    tags=["Evaluations"]
)


# ======================== post method for creating the evaluation run =============================== #
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
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ======================== get method for listing all evaluation runs =============================== #
@router.get(
    "/",
    response_model=list[EvaluationResponse]
)
def list_evaluations(
    run_id: int | None = None,
    db: Session = Depends(get_db)
):
    return evaluation_service.list_evaluation(db, run_id)


# ================== get method for getting the evaluation run by id =============================== #
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
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found"
        )
    return evaluation


# ====================== post method for starting the evaluation run ================================= #
@router.post(
    "/{evaluation_id}/start",
    response_model=EvaluationResponse
)
def start_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    try:
        return evaluation_service.start_evaluation(db, evaluation_id)
    except ValueError as error:
        err_msg = str(error)
        status_code = 404 if "not found" in err_msg.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=err_msg
        )


# ====================== post method for saving the evaluation results ================================ #
@router.post(
    "/{evaluation_id}/result",
    response_model=EvaluationResponse
)
def save_evaluation_result(
    evaluation_id: int,
    result: EvaluationResult,
    db: Session = Depends(get_db)
):
    try:
        return evaluation_service.save_evaluation_result(db, evaluation_id, result)
    except ValueError as error:
        err_msg = str(error)
        status_code = 404 if "not found" in err_msg.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=err_msg
        )


# ================== post method for failed evaluations ================================= #
@router.post(
    "/{evaluation_id}/fail",
    response_model=EvaluationResponse
)
def fail_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    try:
        return evaluation_service.fail_evaluation(db, evaluation_id)
    except ValueError as error:
        err_msg = str(error)
        status_code = 404 if "not found" in err_msg.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=err_msg
        )