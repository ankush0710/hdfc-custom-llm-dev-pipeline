import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.core.auth_dependency import (
    create_access_token,
    decode_access_token,
    hash_password,
    require_roles,
    verify_password,
)
from app.model.user_model import User_Model
from app.schema.auth_schema.auth_schema import RoleUpdate, UserStatusUpdate
from app.routes.auth_routes.auth_routes import update_user_role, update_user_status, VALID_ROLES


class TestAuthAndRBAC(unittest.TestCase):
    def test_1_password_hashing_and_verification(self):
        plain_pwd = "ankush@1234"
        hashed = hash_password(plain_pwd)

        self.assertNotEqual(plain_pwd, hashed)
        self.assertTrue(verify_password(plain_pwd, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_2_jwt_token_encoding_and_decoding_for_all_roles(self):
        roles = ["ADMIN", "DS", "REVIEWER", "VIEWER"]
        for r in roles:
            payload = {"sub": "101", "email": f"{r.lower()}@hdfc.com", "role": r}
            token = create_access_token(payload)
            decoded = decode_access_token(token)

            self.assertEqual(decoded["sub"], "101")
            self.assertEqual(decoded["email"], f"{r.lower()}@hdfc.com")
            self.assertEqual(decoded["role"], r)

    def test_3_user_model_role_defaults_to_viewer(self):
        user = User_Model(
            full_name="New Enterprise User",
            email="user@hdfc.com",
            password_hash=hash_password("Password123!"),
            role="VIEWER",
            is_active=True,
        )
        self.assertEqual(user.role, "VIEWER")
        self.assertTrue(user.is_active)

    def test_4_rbac_viewer_blocked_from_start_training_with_403(self):
        viewer = User_Model(id=10, role="VIEWER", is_active=True)
        checker = require_roles("ADMIN", "DS")

        with self.assertRaises(HTTPException) as ctx:
            checker(viewer)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access Denied", ctx.exception.detail)

    def test_5_rbac_ds_allowed_to_start_training(self):
        ds = User_Model(id=20, role="DS", is_active=True)
        checker = require_roles("ADMIN", "DS")

        authorized = checker(ds)
        self.assertEqual(authorized.id, 20)

    def test_6_rbac_ds_blocked_from_admin_user_management(self):
        ds = User_Model(id=20, role="DS", is_active=True)
        checker = require_roles("ADMIN")

        with self.assertRaises(HTTPException) as ctx:
            checker(ds)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access Denied", ctx.exception.detail)

    def test_7_rbac_reviewer_allowed_for_evaluations_and_blocked_from_training(self):
        reviewer = User_Model(id=30, role="REVIEWER", is_active=True)
        eval_checker = require_roles("ADMIN", "DS", "REVIEWER")
        authorized = eval_checker(reviewer)
        self.assertEqual(authorized.id, 30)

        training_checker = require_roles("ADMIN", "DS")
        with self.assertRaises(HTTPException) as ctx:
            training_checker(reviewer)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_8_rbac_admin_allowed_for_all_actions(self):
        admin = User_Model(id=1, role="ADMIN", is_active=True)

        # Admin can access training, evaluations, deployments, and user management
        self.assertEqual(require_roles("ADMIN", "DS")(admin).id, 1)
        self.assertEqual(require_roles("ADMIN", "DS", "REVIEWER")(admin).id, 1)
        self.assertEqual(require_roles("ADMIN")(admin).id, 1)

    def test_9_valid_roles_set(self):
        self.assertEqual(VALID_ROLES, {"ADMIN", "DS", "REVIEWER", "VIEWER"})

    def test_10_admin_promotion_logic(self):
        db_mock = MagicMock()
        admin_caller = User_Model(id=1, email="admin@hdfc.com", role="ADMIN", is_active=True)
        target_user = User_Model(id=2, email="user@hdfc.com", role="VIEWER", is_active=True)

        db_mock.query.return_value.filter.return_value.first.return_value = target_user

        # Admin promotes target_user to DS
        updated = update_user_role(
            user_id=2,
            payload=RoleUpdate(role="DS"),
            db=db_mock,
            admin=admin_caller,
        )
        self.assertEqual(updated.role, "DS")

        # Admin promotes target_user to ADMIN
        updated_admin = update_user_role(
            user_id=2,
            payload=RoleUpdate(role="ADMIN"),
            db=db_mock,
            admin=admin_caller,
        )
        self.assertEqual(updated_admin.role, "ADMIN")

    def test_11_user_status_deactivation_and_protection(self):
        db_mock = MagicMock()
        admin_caller = User_Model(id=1, email="admin@hdfc.com", role="ADMIN", is_active=True)
        target_user = User_Model(id=5, email="member@hdfc.com", role="DS", is_active=True)

        db_mock.query.return_value.filter.return_value.first.return_value = target_user

        # Admin deactivates target_user
        res = update_user_status(
            user_id=5,
            payload=UserStatusUpdate(is_active=False),
            db=db_mock,
            admin=admin_caller,
        )
        self.assertFalse(res.is_active)

        # Admin cannot deactivate themselves
        db_mock.query.return_value.filter.return_value.first.return_value = admin_caller
        with self.assertRaises(HTTPException) as ctx:
            update_user_status(
                user_id=1,
                payload=UserStatusUpdate(is_active=False),
                db=db_mock,
                admin=admin_caller,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("cannot deactivate their own", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
