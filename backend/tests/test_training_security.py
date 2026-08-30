import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException
import sys
import os

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.training_service.training_service import create_training_run, start_training_run
from app.schema.training_schema.training_schema import TrainingRunCreate
from app.model.dataset_version_model import Dataset_Version_Model
from app.model.training_model import Training_Model


class TestTrainingSecurityProtection(unittest.TestCase):
    """
    Test 7 — Dataset Training Protection
    Verify that a raw dataset cannot be passed directly to training.
    The training API must reject it with an appropriate validation error.
    """

    def test_raw_uploaded_dataset_rejected_by_create_training_run(self):
        db = MagicMock()

        # Mock raw dataset version: uploaded status, raw file path, is_safe_for_training=False
        raw_version = Dataset_Version_Model(
            id=101,
            dataset_id=1,
            version="1.0.0",
            file_name="raw_customer_data.csv",
            file_path="uploads/datasets/raw_customer_data.csv",
            status="Uploaded",
            is_safe_for_training=False,
            pii_scan_status="PENDING"
        )

        db.query.return_value.filter.return_value.first.return_value = raw_version

        request_data = TrainingRunCreate(
            dataset_version_id=101,
            base_model="Qwen/Qwen3-0.6B",
            training_method="lora",
            epochs=1,
            learning_rate=0.0002,
            batch_size=1
        )

        with self.assertRaises(HTTPException) as ctx:
            create_training_run(db, request_data)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("not safe for training", ctx.exception.detail)
        self.assertIn("strictly prohibited on raw datasets", ctx.exception.detail)

    def test_raw_file_path_rejected_even_if_status_is_processed(self):
        db = MagicMock()

        # Mock malicious / mismatched version pointing to uploads/ directory
        tampered_version = Dataset_Version_Model(
            id=102,
            dataset_id=1,
            version="1.0.0",
            file_name="tampered.csv",
            file_path="uploads/datasets/tampered.csv",
            status="Processed",
            is_safe_for_training=True, # Even if boolean flag is set, raw uploads path is blocked
            pii_scan_status="PASSED"
        )

        db.query.return_value.filter.return_value.first.return_value = tampered_version

        request_data = TrainingRunCreate(
            dataset_version_id=102,
            base_model="Qwen/Qwen3-0.6B",
            training_method="lora",
            epochs=1,
            learning_rate=0.0002,
            batch_size=1
        )

        with self.assertRaises(HTTPException) as ctx:
            create_training_run(db, request_data)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("strictly prohibited on raw datasets", ctx.exception.detail)

    def test_sanitized_processed_dataset_accepted(self):
        db = MagicMock()

        # Mock properly processed and sanitized dataset version in storage/processed/
        safe_processed_version = Dataset_Version_Model(
            id=103,
            dataset_id=1,
            version="1.0.0-cleaned",
            file_name="dataset_1_processed_safe.csv",
            file_path="storage/processed/dataset_1_processed_safe.csv",
            status="Processed",
            is_safe_for_training=True,
            pii_scan_status="PASSED"
        )

        db.query.return_value.filter.return_value.first.return_value = safe_processed_version

        request_data = TrainingRunCreate(
            dataset_version_id=103,
            base_model="Qwen/Qwen3-0.6B",
            training_method="lora",
            epochs=1,
            learning_rate=0.0002,
            batch_size=1
        )

        # Should not raise exception
        run = create_training_run(db, request_data)
        self.assertIsNotNone(run)
        self.assertEqual(run.dataset_version_id, 103)


if __name__ == "__main__":
    unittest.main()
