from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth_dependency import get_current_user, require_permission, require_roles
from app.dbConfig.database_config import get_db
from app.model.user_model import User_Model
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
    current_user: User_Model = Depends(require_permission("model:deploy")),
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
    current_user: User_Model = Depends(require_permission("deployment:read")),
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
    current_user: User_Model = Depends(require_permission("deployment:read")),
):
    service = DeploymentService(db)
    try:
        return service.get_deployment_by_id(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{deployment_id}/rollback",
    response_model=Deployment_Response,
)
def rollback_deployment(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.rollback_deployment(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{deployment_id}/undeploy",
    response_model=Deployment_Response,
)
def undeploy_model(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.undeploy_model(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{deployment_id}/unload",
    response_model=Deployment_Response,
)
def unload_model(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.undeploy_model(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{deployment_id}/reload",
    response_model=Deployment_Response,
)
def reload_model(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.reload_deployment(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{deployment_id}/restart",
    response_model=Deployment_Response,
)
def restart_model(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.restart_deployment(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{deployment_id}/start",
    response_model=Deployment_Response,
)
def start_model(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.start_deployment(deployment_id)
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
    current_user: User_Model = Depends(require_permission("model:deploy")),
):
    service = DeploymentService(db)
    try:
        return service.undeploy_model(deployment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
