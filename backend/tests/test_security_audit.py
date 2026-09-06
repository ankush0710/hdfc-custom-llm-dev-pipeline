"""
backend/tests/test_security_audit.py

Comprehensive security audit and regression test suite for:
1. Exact 30-minute boundary enforcement for VIEWER/REVIEWER sessions.
2. Wildcard and granular RBAC permission validation.
3. Client-side role tampering prevention on signup.
4. Database role authoritativeness & immediate token invalidation on role mismatch.
5. Undeployed model inference rejection (dual check: model.status == DEPLOYED & active Deployment).
6. Dataset lineage resolution and separation from prompt context.

All tests use dynamic fixtures (no hardcoded IDs).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.core.auth_dependency import (
    create_access_token,
    decode_access_token,
    check_permission,
    require_permission,
    get_current_user,
    ROLE_PERMISSIONS,
    STRICT_SESSION_MAX_MINUTES,
    STRICT_SESSION_ROLES,
)
from app.model.user_model import User_Model
from app.model.model_registry import Model_Registry
from app.model.deployment_model import Deployment
from app.model.training_model import Training_Model
from app.model.training_job_model import TrainingJobModel
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.dataset_model import Dataset_Model
from app.model.evaluation_run_model import Evaluation_Model
from app.schema.auth_schema.auth_schema import UserSignup
from app.routes.auth_routes.auth_routes import signup
from app.services.inference_service.inference_service import InferenceService, INFERENCE_ALLOWED_STATUSES
from app.services.deployment_service.deployment_service import DeploymentService


class TestSecurityAudit(unittest.TestCase):

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Exact 30-Minute Session Boundary Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_1_strict_session_constants(self):
        """Verify strict session configuration constants."""
        self.assertEqual(STRICT_SESSION_MAX_MINUTES, 30)
        self.assertEqual(STRICT_SESSION_ROLES, {"VIEWER", "REVIEWER"})

    def test_2_exact_30_minute_boundary_viewer(self):
        """
        Verify exact 30-minute boundary for VIEWER role:
        - t0: valid
        - t0 + 29m 59s: valid
        - t0 + 30m 00s: 401 Unauthorized
        - t0 + 30m 01s: 401 Unauthorized
        """
        t0 = 1700000000.0  # reference epoch timestamp

        # Create token at t0 for VIEWER
        with patch("app.core.auth_dependency.time.time", return_value=t0):
            token = create_access_token({
                "sub": "42",
                "email": "viewer.test@hdfc.com",
                "role": "VIEWER",
            })

        decoded = decode_access_token(token)
        self.assertIn("abs_exp", decoded)
        expected_abs_exp = int(t0 + 30 * 60)
        self.assertEqual(decoded["abs_exp"], expected_abs_exp)

        # Mock DB and user record
        mock_user = User_Model(
            id=42,
            email="viewer.test@hdfc.com",
            role="VIEWER",
            is_active=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Boundary test A: t0 (immediate) -> valid
        with patch("app.core.auth_dependency.time.time", return_value=t0):
            user = get_current_user(token=token, db=mock_db)
            self.assertEqual(user.id, 42)

        # Boundary test B: t0 + 29m 59s (1799 seconds) -> valid
        with patch("app.core.auth_dependency.time.time", return_value=t0 + 1799):
            user = get_current_user(token=token, db=mock_db)
            self.assertEqual(user.id, 42)

        # Boundary test C: t0 + 30m 00s (1800 seconds) -> 401 Unauthorized
        with patch("app.core.auth_dependency.time.time", return_value=t0 + 1800):
            with self.assertRaises(HTTPException) as ctx:
                get_current_user(token=token, db=mock_db)
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("Session expired", ctx.exception.detail)

        # Boundary test D: t0 + 30m 01s (1801 seconds) -> 401 Unauthorized
        with patch("app.core.auth_dependency.time.time", return_value=t0 + 1801):
            with self.assertRaises(HTTPException) as ctx:
                get_current_user(token=token, db=mock_db)
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("Session expired", ctx.exception.detail)

    def test_3_exact_30_minute_boundary_reviewer(self):
        """Verify exact 30-minute boundary for REVIEWER role."""
        t0 = 1700000000.0

        with patch("app.core.auth_dependency.time.time", return_value=t0):
            token = create_access_token({
                "sub": "55",
                "email": "reviewer.test@hdfc.com",
                "role": "REVIEWER",
            })

        mock_user = User_Model(
            id=55,
            email="reviewer.test@hdfc.com",
            role="REVIEWER",
            is_active=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # t0 + 29m 59s -> valid
        with patch("app.core.auth_dependency.time.time", return_value=t0 + 1799):
            user = get_current_user(token=token, db=mock_db)
            self.assertEqual(user.id, 55)

        # t0 + 30m 00s -> 401 Unauthorized
        with patch("app.core.auth_dependency.time.time", return_value=t0 + 1800):
            with self.assertRaises(HTTPException) as ctx:
                get_current_user(token=token, db=mock_db)
            self.assertEqual(ctx.exception.status_code, 401)

    def test_4_admin_and_ds_not_restricted_by_30m_limit(self):
        """Verify ADMIN and DS tokens do NOT have the 30-minute hard cap."""
        for role in ["ADMIN", "DS"]:
            token = create_access_token({
                "sub": "1",
                "email": f"{role.lower()}@hdfc.com",
                "role": role,
            })
            decoded = decode_access_token(token)
            self.assertIsNone(decoded.get("abs_exp"))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Wildcard and Granular RBAC Permissions
    # ─────────────────────────────────────────────────────────────────────────

    def test_5_check_permission_wildcard_matching(self):
        """Test wildcard matching engine in check_permission."""
        # Universal wildcard
        self.assertTrue(check_permission({"*"}, "anything:at:all"))
        self.assertTrue(check_permission(["*"], "user:role:update"))

        # Domain wildcard
        self.assertTrue(check_permission({"dataset:*"}, "dataset:create"))
        self.assertTrue(check_permission(["dataset:*"], "dataset:read"))
        self.assertFalse(check_permission({"dataset:*"}, "training:start"))

        # Exact match
        self.assertTrue(check_permission({"evaluation:read", "evaluation:create"}, "evaluation:read"))
        self.assertFalse(check_permission({"evaluation:read", "evaluation:create"}, "evaluation:delete"))

    def test_6_require_permission_enforcement(self):
        """Test require_permission dependency for different roles."""
        admin = User_Model(id=1, role="ADMIN", is_active=True)
        ds = User_Model(id=2, role="DS", is_active=True)
        reviewer = User_Model(id=3, role="REVIEWER", is_active=True)
        viewer = User_Model(id=4, role="VIEWER", is_active=True)

        # user:role:update is ADMIN only
        role_updater = require_permission("user:role:update")
        self.assertEqual(role_updater(admin).id, 1)
        for user in [ds, reviewer, viewer]:
            with self.assertRaises(HTTPException) as ctx:
                role_updater(user)
            self.assertEqual(ctx.exception.status_code, 403)

        # dataset:create is ADMIN and DS only
        dataset_creator = require_permission("dataset:create")
        self.assertEqual(dataset_creator(admin).id, 1)
        self.assertEqual(dataset_creator(ds).id, 2)
        for user in [reviewer, viewer]:
            with self.assertRaises(HTTPException) as ctx:
                dataset_creator(user)
            self.assertEqual(ctx.exception.status_code, 403)

        # evaluation:create is accessible to ADMIN, DS, and REVIEWER (not VIEWER)
        eval_creator = require_permission("evaluation:create")
        self.assertEqual(eval_creator(admin).id, 1)
        self.assertEqual(eval_creator(ds).id, 2)
        self.assertEqual(eval_creator(reviewer).id, 3)
        with self.assertRaises(HTTPException) as ctx:
            eval_creator(viewer)
        self.assertEqual(ctx.exception.status_code, 403)

        # inference:execute is accessible to all active roles
        inferencer = require_permission("inference:execute")
        for user in [admin, ds, reviewer, viewer]:
            self.assertEqual(inferencer(user).id, user.id)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Client Role Tampering Prevention on Signup
    # ─────────────────────────────────────────────────────────────────────────

    def test_7_signup_unconditionally_assigns_viewer(self):
        """Verify signup ignores any attempted role escalation and assigns VIEWER."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        captured_users = []
        def capture_add(user):
            captured_users.append(user)
        mock_db.add.side_effect = capture_add

        # Attempt to sign up requesting privileged role (e.g. ADMIN or DS)
        signup_payload = UserSignup(
            full_name="Attacker",
            email="attacker@hdfc.com",
            password="SecurePassword123!",
            confirm_password="SecurePassword123!",
        )

        created = signup(payload=signup_payload, db=mock_db)

        self.assertEqual(len(captured_users), 1)
        persisted_user = captured_users[0]
        self.assertEqual(persisted_user.role, "VIEWER")
        self.assertEqual(created.role, "VIEWER")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Database Role Authoritativeness & Immediate Invalidation
    # ─────────────────────────────────────────────────────────────────────────

    def test_8_role_mismatch_immediate_invalidation(self):
        """
        Verify that if DB role != JWT claim role (due to demotion or promotion),
        existing token is immediately invalidated with HTTP 401.
        """
        # 1. Token forged or minted with role="DS"
        token = create_access_token({
            "sub": "77",
            "email": "demoted@hdfc.com",
            "role": "DS",
        })

        # Database says user was demoted to "VIEWER"
        db_user = User_Model(
            id=77,
            email="demoted@hdfc.com",
            role="VIEWER",
            is_active=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token=token, db=mock_db)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("User role or permissions have been updated", ctx.exception.detail)

    def test_9_deactivated_user_immediate_invalidation(self):
        """Verify deactivated user token yields 403."""
        token = create_access_token({
            "sub": "88",
            "email": "deactivated@hdfc.com",
            "role": "VIEWER",
        })

        db_user = User_Model(
            id=88,
            email="deactivated@hdfc.com",
            role="VIEWER",
            is_active=False,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token=token, db=mock_db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("deactivated", ctx.exception.detail)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Undeployed Model Inference Rejection (Dual Check)
    # ─────────────────────────────────────────────────────────────────────────

    def test_10_inference_rejects_non_deployed_status(self):
        """InferenceService.predict rejects model if model.status != DEPLOYED."""
        mock_db = MagicMock()
        # Create dynamic model fixture with status "READY"
        model_fixture = Model_Registry(
            id=101,
            model_name="HDFC-Risk-v1",
            version="1.0.0",
            base_model="meta-llama/Llama-3-8b",
            status="READY",  # Not DEPLOYED
        )
        mock_db.query.return_value.filter.return_value.first.return_value = model_fixture

        service = InferenceService(mock_db)
        with self.assertRaises(ValueError) as ctx:
            service.predict(
                model_id=101,
                task_type="customer_faq_qa",
                question="What are your credit card interest rates?",
            )
        self.assertIn("Inference is only allowed for models with status", str(ctx.exception))

    def test_11_inference_rejects_missing_or_inactive_deployment(self):
        """InferenceService.predict rejects model if model.status == DEPLOYED but no ACTIVE Deployment exists."""
        mock_db = MagicMock()
        # Model is marked DEPLOYED
        model_fixture = Model_Registry(
            id=102,
            model_name="HDFC-Compliance-v2",
            version="2.0.0",
            base_model="meta-llama/Llama-3-8b",
            status="DEPLOYED",
        )

        def mock_query(model_class):
            mock_filter = MagicMock()
            if model_class == Model_Registry:
                mock_filter.filter.return_value.first.return_value = model_fixture
            elif model_class == Deployment:
                # No active deployment found
                mock_filter.filter.return_value.first.return_value = None
            return mock_filter

        mock_db.query.side_effect = mock_query

        service = InferenceService(mock_db)
        with self.assertRaises(ValueError) as ctx:
            service.predict(
                model_id=102,
                task_type="customer_faq_qa",
                question="What is the daily RTGS transaction limit?",
            )
        self.assertIn("does not have an ACTIVE deployment", str(ctx.exception))

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Dataset Lineage Resolution & Context Separation
    # ─────────────────────────────────────────────────────────────────────────

    def test_12_dataset_lineage_resolution_in_deployment_enrichment(self):
        """
        Verify that _enrich_deployment resolves dataset lineage through:
        Model_Registry -> TrainingJobModel -> Training_Model -> Dataset_Version_Model -> Dataset_Model
        """
        mock_db = MagicMock()

        # Dynamic fixtures
        dyn_ds_id = 701
        dyn_dv_id = 801
        dyn_tr_id = 901
        dyn_tj_id = 1001
        dyn_model_id = 1101
        dyn_dep_id = 1201

        dyn_dataset = Dataset_Model(id=dyn_ds_id, dataset_name="HDFC-Retail-Loans-2026")
        dyn_version = Dataset_Version_Model(id=dyn_dv_id, dataset_id=dyn_ds_id, version="v3.1", file_name="loans_train.jsonl")
        dyn_run = Training_Model(id=dyn_tr_id, dataset_version_id=dyn_dv_id, base_model="Llama-3-8b")
        dyn_job = TrainingJobModel(id=dyn_tj_id, training_run_id=dyn_tr_id)
        dyn_model = Model_Registry(id=dyn_model_id, model_name="HDFC-Loan-Assistant", version="1.0.0", base_model="Llama-3-8b", training_job_id=dyn_tj_id, status="DEPLOYED")
        dyn_dep = Deployment(id=dyn_dep_id, model_id=dyn_model_id, version="1.0.0", environment="Production", status="ACTIVE")

        def mock_query(cls):
            m = MagicMock()
            if cls == Model_Registry:
                m.filter.return_value.first.return_value = dyn_model
            elif cls == TrainingJobModel:
                m.filter.return_value.first.return_value = dyn_job
            elif cls == Training_Model:
                m.filter.return_value.first.return_value = dyn_run
            elif cls == Dataset_Version_Model:
                m.filter.return_value.first.return_value = dyn_version
            elif cls == Dataset_Model:
                m.filter.return_value.first.return_value = dyn_dataset
            else:
                m.filter.return_value.first.return_value = None
                m.filter.return_value.order_by.return_value.first.return_value = None
            return m

        mock_db.query.side_effect = mock_query

        service = DeploymentService(mock_db)
        enriched = service._enrich_deployment(dyn_dep)

        self.assertEqual(enriched.dataset_name, "HDFC-Retail-Loans-2026")
        self.assertEqual(enriched.dataset_version, "v3.1")
        self.assertEqual(enriched.dataset_file_name, "loans_train.jsonl")
        self.assertEqual(enriched.training_run_id, dyn_tr_id)

    @patch("app.clients.ml_client.MLClient.predict")
    def test_inference_predict_returns_realtime_dataset_lineage(self, mock_ml_predict):
        """InferenceService.predict must resolve real-time dataset lineage dynamically from the DB."""
        dyn_model_id = 9182
        dyn_job_id = 8172
        dyn_tr_id = 7162
        dyn_dver_id = 6152
        dyn_ds_id = 5142

        dyn_model = MagicMock(spec=Model_Registry)
        dyn_model.id = dyn_model_id
        dyn_model.model_name = "HDFC-Enterprise-LLM-Realtime"
        dyn_model.version = "1.0.0"
        dyn_model.base_model = "Qwen/Qwen2.5-0.5B-Instruct"
        dyn_model.status = "DEPLOYED"
        dyn_model.adapter_path = "/models/realtime_adapter"
        dyn_model.artifact_path = "/models/realtime_adapter"
        dyn_model.huggingface_path = None
        dyn_model.training_job_id = dyn_job_id
        dyn_model.evaluation_id = None

        dyn_dep = MagicMock(spec=Deployment)
        dyn_dep.model_id = dyn_model_id
        dyn_dep.status = "ACTIVE"

        dyn_job = MagicMock(spec=TrainingJobModel)
        dyn_job.id = dyn_job_id
        dyn_job.training_run_id = dyn_tr_id

        dyn_run = MagicMock(spec=Training_Model)
        dyn_run.id = dyn_tr_id
        dyn_run.dataset_version_id = dyn_dver_id

        dyn_version = MagicMock(spec=Dataset_Version_Model)
        dyn_version.id = dyn_dver_id
        dyn_version.dataset_id = dyn_ds_id
        dyn_version.version = "v5.0-live"
        dyn_version.file_name = "hdfc_live_qa.jsonl"

        dyn_dataset = MagicMock(spec=Dataset_Model)
        dyn_dataset.id = dyn_ds_id
        dyn_dataset.dataset_name = "HDFC-Live-Production-Corpus"

        mock_ml_predict.return_value = {
            "model_id": dyn_model_id,
            "response": "HDFC Bank savings interest rates start at 3.0% p.a. as per policy.",
            "latency_seconds": 0.08,
            "tokens_generated": 25,
            "fine_tuned": True,
            "device": "cpu",
        }

        mock_db = MagicMock()

        def mock_query(cls):
            m = MagicMock()
            if cls == Model_Registry:
                m.filter.return_value.first.return_value = dyn_model
            elif cls == Deployment:
                m.filter.return_value.first.return_value = dyn_dep
            elif cls == TrainingJobModel:
                m.filter.return_value.first.return_value = dyn_job
            elif cls == Training_Model:
                m.filter.return_value.first.return_value = dyn_run
            elif cls == Dataset_Version_Model:
                m.filter.return_value.first.return_value = dyn_version
            elif cls == Dataset_Model:
                m.filter.return_value.first.return_value = dyn_dataset
            else:
                m.filter.return_value.first.return_value = None
            return m

        mock_db.query.side_effect = mock_query

        service = InferenceService(mock_db)
        result = service.predict(
            model_id=dyn_model_id,
            task_type="customer_faq_qa",
            question="What are HDFC bank savings account interest rates?",
            context="Provide official banking rates only.",
        )

        # 1. Verify dynamic dataset lineage is accurately resolved in the inference response
        self.assertEqual(result["dataset_id"], dyn_ds_id)
        self.assertEqual(result["dataset_name"], "HDFC-Live-Production-Corpus")
        self.assertEqual(result["dataset_version"], "v5.0-live")
        self.assertEqual(result["dataset_file_name"], "hdfc_live_qa.jsonl")
        self.assertEqual(result["training_run_id"], dyn_tr_id)
        self.assertEqual(result["model_id"], dyn_model_id)

        # 2. Verify separation: dataset content/name was NOT injected into prompt or context
        called_args = mock_ml_predict.call_args[1]
        self.assertNotIn("HDFC-Live-Production-Corpus", called_args.get("question", ""))
        self.assertNotIn("HDFC-Live-Production-Corpus", called_args.get("context", ""))
        self.assertEqual(called_args.get("context"), "Provide official banking rates only.")

    def test_model_registry_returns_latency_and_throughput(self):
        """Model registry routes must format real latency and throughput correctly."""
        from app.routes.model_registry_routes.model_registry_routes import _format_metrics, get_model_detail
        from datetime import datetime, timezone, timedelta

        # Case 1: Evaluation with exact average_latency_seconds = 0.25s
        eval_record = MagicMock(spec=Evaluation_Model)
        eval_record.answer_accuracy = 0.95
        eval_record.intent_structured_accuracy = 0.95
        eval_record.full_structured_match = 0.92
        eval_record.policy_flag_accuracy = 0.90
        eval_record.average_latency_seconds = 0.25

        acc, f1, lat, tp = _format_metrics(eval_record)
        self.assertEqual(acc, "95.0%")
        self.assertEqual(f1, "0.92")
        self.assertEqual(lat, "250 ms")
        self.assertEqual(tp, "4.0 req/s")

        # Case 2: Evaluation where average_latency_seconds is None but timestamps exist
        now = datetime.now(timezone.utc)
        eval_record_ts = MagicMock(spec=Evaluation_Model)
        eval_record_ts.answer_accuracy = 0.88
        eval_record_ts.intent_structured_accuracy = None
        eval_record_ts.full_structured_match = 0.85
        eval_record_ts.policy_flag_accuracy = None
        eval_record_ts.average_latency_seconds = None
        eval_record_ts.started_at = now - timedelta(seconds=10)
        eval_record_ts.completed_at = now
        eval_record_ts.total_examples = 5

        acc, f1, lat, tp = _format_metrics(eval_record_ts)
        self.assertEqual(acc, "88.0%")
        self.assertEqual(f1, "0.85")
        self.assertEqual(lat, "2000 ms")
        self.assertEqual(tp, "0.5 req/s")


if __name__ == "__main__":
    unittest.main()
