import datetime
from sqlalchemy.orm import Session
from app.model.deployment_model import Deployment
from app.model.model_registry import Model_Registry


class DeploymentService:

    def __init__(self, db: Session):
        self.db = db

    def _enrich_deployment(self, deployment: Deployment) -> Deployment:
        if not deployment:
            return None

        model = (
            self.db.query(Model_Registry)
            .filter(Model_Registry.id == deployment.model_id)
            .first()
        )
        if model:
            deployment.model_name = model.model_name
            deployment.base_model = model.base_model
            slug = model.model_name.lower().replace(" ", "-").replace("_", "-")
            ver_slug = deployment.version.replace(".", "-")
            if not deployment.endpoint or deployment.endpoint == "/inference/predict":
                deployment.endpoint = f"https://inference.capital.ai/v1/models/{slug}-v{ver_slug}/generate"
        else:
            deployment.model_name = f"Model #{deployment.model_id}"
            deployment.base_model = None
            if not deployment.endpoint:
                deployment.endpoint = f"https://inference.capital.ai/v1/models/model-{deployment.model_id}/generate"

        return deployment

    def deploy_model(
        self,
        model_id: int,
        version: str,
        environment: str = "Production",
    ):
        model = (
            self.db.query(Model_Registry)
            .filter(Model_Registry.id == model_id)
            .first()
        )

        if not model:
            raise ValueError(f"Model {model_id} not found in Model Registry")

        valid_deploy_statuses = {"READY", "APPROVED", "TRAINED", "DEPLOYED", "ACTIVE", "CREATED", "EVALUATED"}
        if str(model.status).upper() not in valid_deploy_statuses:
            raise ValueError(
                f"Model status '{model.status}' cannot be deployed. Valid statuses: {sorted(valid_deploy_statuses)}"
            )

        slug = model.model_name.lower().replace(" ", "-").replace("_", "-")
        ver_slug = str(version).replace(".", "-")
        serving_endpoint = f"https://inference.capital.ai/v1/models/{slug}-v{ver_slug}/generate"

        deployment = Deployment(
            model_id=model_id,
            version=version,
            environment=environment or "Production",
            status="ACTIVE",
            endpoint=serving_endpoint,
        )

        # Update model status in registry to DEPLOYED
        model.status = "DEPLOYED"

        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)

        return self._enrich_deployment(deployment)

    def list_deployments(self):
        items = (
            self.db.query(Deployment)
            .order_by(Deployment.created_at.desc())
            .all()
        )
        return [self._enrich_deployment(item) for item in items]

    def get_deployment_by_id(self, deployment_id: int):
        deployment = (
            self.db.query(Deployment)
            .filter(Deployment.id == deployment_id)
            .first()
        )
        if deployment:
            return self._enrich_deployment(deployment)
        return None

    def undeploy_model(self, deployment_id: int):
        deployment = (
            self.db.query(Deployment)
            .filter(Deployment.id == deployment_id)
            .first()
        )
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment.status = "STOPPED"

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
        return self._enrich_deployment(deployment)

    def restart_deployment(self, deployment_id: int):
        deployment = (
            self.db.query(Deployment)
            .filter(Deployment.id == deployment_id)
            .first()
        )
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment.status = "ACTIVE"
        self.db.commit()
        self.db.refresh(deployment)
        return self._enrich_deployment(deployment)

    def reload_deployment(self, deployment_id: int):
        deployment = (
            self.db.query(Deployment)
            .filter(Deployment.id == deployment_id)
            .first()
        )
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment.status = "ACTIVE"
        self.db.commit()
        self.db.refresh(deployment)
        return self._enrich_deployment(deployment)

    def start_deployment(self, deployment_id: int):
        deployment = (
            self.db.query(Deployment)
            .filter(Deployment.id == deployment_id)
            .first()
        )
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment.status = "ACTIVE"
        model = self.db.query(Model_Registry).filter(Model_Registry.id == deployment.model_id).first()
        if model:
            model.status = "DEPLOYED"

        self.db.commit()
        self.db.refresh(deployment)
        return self._enrich_deployment(deployment)