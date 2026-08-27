import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.model.model_registry import Model_Registry
from app.services.deployment_service.deployment_service import DeploymentService


class TestQualityGateAndDeployment(unittest.TestCase):
    def test_deployment_blocked_for_rejected_model(self):
        mock_db = MagicMock()
        rejected_model = Model_Registry(
            id=99,
            model_name="rejected_llm_model",
            version="1.0",
            base_model="Qwen/Qwen3-0.6B",
            status="REJECTED",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = rejected_model

        service = DeploymentService(mock_db)
        with self.assertRaises(ValueError) as ctx:
            service.deploy_model(99, "1.0", "Production")

        self.assertIn("REJECTED by the Quality Gate", str(ctx.exception))

    def test_deployment_blocked_for_unapproved_created_model(self):
        mock_db = MagicMock()
        unapproved_model = Model_Registry(
            id=100,
            model_name="unapproved_model",
            version="1.0",
            base_model="Qwen/Qwen3-0.6B",
            status="CREATED",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = unapproved_model

        service = DeploymentService(mock_db)
        with self.assertRaises(ValueError) as ctx:
            service.deploy_model(100, "1.0", "Production")

        self.assertIn("must pass Quality Gate evaluation", str(ctx.exception))

    def test_deployment_allowed_for_approved_model(self):
        mock_db = MagicMock()
        approved_model = Model_Registry(
            id=101,
            model_name="approved_llm_model",
            version="1.0",
            base_model="Qwen/Qwen3-0.6B",
            status="APPROVED",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = approved_model

        service = DeploymentService(mock_db)
        deployment = service.deploy_model(101, "1.0", "Production")

        self.assertEqual(deployment.status, "ACTIVE")
        self.assertEqual(approved_model.status, "DEPLOYED")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
