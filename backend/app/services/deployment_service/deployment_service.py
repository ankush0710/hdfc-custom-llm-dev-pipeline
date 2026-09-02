import datetime
from sqlalchemy.orm import Session
from app.model.deployment_model import Deployment
from app.model.evaluation_run_model import Evaluation_Model
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

        # Resolve latency from real evaluation benchmarks
        eval_record = None
        if model and getattr(model, "evaluation_id", None):
            eval_record = (
                self.db.query(Evaluation_Model)
                .filter(Evaluation_Model.evaluation_id == model.evaluation_id)
                .first()
            )
        if not eval_record and deployment.model_id:
            eval_record = (
                self.db.query(Evaluation_Model)
                .filter(
                    Evaluation_Model.model_id == deployment.model_id,
                    Evaluation_Model.evaluation_status == "COMPLETED",
                )
                .order_by(Evaluation_Model.evaluation_id.desc())
                .first()
            )

        if eval_record and eval_record.average_latency_seconds is not None:
            sec = float(eval_record.average_latency_seconds)
            ms = round(sec * 1000, 1)
            deployment.average_latency_ms = ms
            if sec < 1.0:
                deployment.latency = f"{int(ms) if ms.is_integer() else ms} ms"
            else:
                deployment.latency = f"{round(sec, 2)} s"
        else:
            deployment.average_latency_ms = None
            deployment.latency = None

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

        from app.constants.quality_gate_config import VALID_DEPLOYABLE_STATUSES

        status_upper = str(model.status).upper()
        if status_upper in {"REJECTED", "FAILED"}:
            raise ValueError(
                f"Deployment blocked: Model #{model_id} ({model.model_name}) was REJECTED by the Quality Gate evaluation."
            )
        if status_upper not in VALID_DEPLOYABLE_STATUSES:
            raise ValueError(
                f"Deployment blocked: Model #{model_id} status is '{model.status}'. "
                f"A model must pass Quality Gate evaluation (Status: APPROVED / READY) before deployment."
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