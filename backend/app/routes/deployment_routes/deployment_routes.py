# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.schema.deployment_schema.deployment_schema import (
    Deployment_Create,
    Deployment_Response,
)
from app.services.deployment_service.deployment_service import (
    DeploymentService,
)


router = APIRouter(
    prefix="/deployments",
    tags=["Deployments"],
)


@router.post(
    "",
    response_model=Deployment_Response,
)
def deploy_model(
    payload: Deployment_Create,
    db: Session = Depends(get_db),
):

    service = DeploymentService(db)

    try:
        return service.deploy_model(
            model_id=payload.model_id,
            version=payload.version,
            environment=payload.environment,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )