from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.schema.model_registry.model_registry import (
    Model_Create,
    Model_Response,
    Model_Update_Status,
)
from app.services.model_registry_service.model_registry_service import (
    create_model,
    get_model,
    list_model,
    update_status,
)

router = APIRouter(
    prefix="/models",
    tags=["Model Registry"],
)


@router.post(
    "",
    response_model=Model_Response,
)
def register_model(
    payload: Model_Create,
    db: Session = Depends(get_db),
):

    try:
        return create_model(
            db,
            payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[Model_Response],
)
def get_models(
    db: Session = Depends(get_db),
):

    return list_model(db)


@router.get(
    "/{model_id}",
    response_model=Model_Response,
)
def get_model_by_id(
    model_id: int,
    db: Session = Depends(get_db),
):

    model = get_model(
        db,
        model_id,
    )

    if not model:
        raise HTTPException(
            status_code=404,
            detail="Model not found",
        )

    return model


@router.patch(
    "/{model_id}/status",
    response_model=Model_Response,
)
def change_model_status(
    model_id: int,
    payload: Model_Update_Status,
    db: Session = Depends(get_db),
):

    try:

        return update_status(
            db,
            model_id,
            payload.status,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )