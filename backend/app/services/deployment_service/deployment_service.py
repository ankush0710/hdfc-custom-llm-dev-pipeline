# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from app.model.deployment_model import Deployment
# pyrefly: ignore [missing-import]
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
            .filter(
                Model_Registry.id == model_id
            )
            .first()
        )

        if not model:
            raise ValueError(
                f"Model {model_id} not found"
            )

        # Replace this condition with
        # your actual Model Registry status field.
        if model.status != "READY":
            raise ValueError(
                "Only READY models can be deployed"
            )

        deployment = Deployment(
            model_id=model_id,
            version=version,
            environment=environment,
            status="STARTING",
        )

        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)

        return deployment