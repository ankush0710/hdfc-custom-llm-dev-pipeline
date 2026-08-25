from fastapi import APIRouter, Depends, HTTPException
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


@router.get(
    "",
    response_model=list[Deployment_Response],
)
def list_deployments(
    db: Session = Depends(get_db),
):
    service = DeploymentService(db)
    return service.list_deployments()


@router.get(
    "/{deployment_id}",
    response_model=Deployment_Response,
)
def get_deployment(
    deployment_id: int,
    db: Session = Depends(get_db),
):
    service = DeploymentService(db)
    deployment = service.get_deployment_by_id(deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=404,
            detail=f"Deployment with id {deployment_id} not found",
        )
    return deployment


@router.post(
    "/{deployment_id}/undeploy",
    response_model=Deployment_Response,
)
def undeploy_model(
    deployment_id: int,
    db: Session = Depends(get_db),
):
    service = DeploymentService(db)
    try:
        return service.undeploy_model(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.delete(
    "/{deployment_id}",
    response_model=Deployment_Response,
)
def delete_deployment(
    deployment_id: int,
    db: Session = Depends(get_db),
):
    service = DeploymentService(db)
    try:
        return service.undeploy_model(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )