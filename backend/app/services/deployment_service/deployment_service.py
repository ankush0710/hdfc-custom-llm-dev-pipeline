from sqlalchemy.orm import Session
from app.model.deployment_model import Deployment
from app.model.model_registry import Model_Registry


class DeploymentService:

    def __init__(self, db: Session):
        self.db = db

    def deploy_model(
        self,
        model_id: int,
        version: str,
        environment: str = "development",
    ):
        model = (
            self.db.query(Model_Registry)
            .filter(Model_Registry.id == model_id)
            .first()
        )

        if not model:
            raise ValueError(f"Model {model_id} not found in Model Registry")

        valid_deploy_statuses = {"READY", "APPROVED", "TRAINED", "DEPLOYED"}
        if model.status not in valid_deploy_statuses:
            raise ValueError(
                f"Model status '{model.status}' cannot be deployed. Valid statuses: {sorted(valid_deploy_statuses)}"
            )

        # Standard serving endpoint URL
        serving_endpoint = "/inference/predict"

        deployment = Deployment(
            model_id=model_id,
            version=version,
            environment=environment,
            status="ACTIVE",
            endpoint=serving_endpoint,
        )

        # Update model status in registry to DEPLOYED
        model.status = "DEPLOYED"

        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)

        return deployment

    def list_deployments(self):
        return (
            self.db.query(Deployment)
            .order_by(Deployment.created_at.desc())
            .all()
        )

    def get_deployment_by_id(self, deployment_id: int):
        return (
            self.db.query(Deployment)
            .filter(Deployment.id == deployment_id)
            .first()
        )

    def undeploy_model(self, deployment_id: int):
        deployment = self.get_deployment_by_id(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment.status = "STOPPED"

        # Check if other active deployments exist for this model
        active_other = (
            self.db.query(Deployment)
            .filter(
                Deployment.model_id == deployment.model_id,
                Deployment.id != deployment_id,
                Deployment.status == "ACTIVE"
            )
            .first()
        )

        if not active_other:
            model = self.db.query(Model_Registry).filter(Model_Registry.id == deployment.model_id).first()
            if model and model.status == "DEPLOYED":
                model.status = "READY"

        self.db.commit()
        self.db.refresh(deployment)
        return deployment