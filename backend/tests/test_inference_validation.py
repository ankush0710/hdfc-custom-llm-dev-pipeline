"""
backend/tests/test_inference_validation.py

Unit tests for inference request contract validation, error mapping,
request_id propagation, and transient retry handling.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

from app.clients.ml_client import MLClient
from app.schema.inference_schema.inference_schema import (
    InferenceRequest,
    SUPPORTED_TASK_TYPES,
)
from app.services.inference_service.inference_service import InferenceService


class TestInferenceValidation(unittest.TestCase):
    """Verify task_type validation and request contracts across inference flow."""

    def test_invalid_task_type_rejected_by_schema(self):
        """'inference' or arbitrary strings must fail schema validation immediately."""
        with self.assertRaises(ValidationError) as ctx:
            InferenceRequest(
                model_id=1,
                task_type="inference",
                question="What is an FD?",
            )
        err_str = str(ctx.exception)
        self.assertIn("The selected task type 'inference' is not supported", err_str)
        self.assertIn("customer_faq_qa", err_str)

    def test_all_supported_task_types_accepted_by_schema(self):
        """All 4 official task types must pass validation without errors."""
        for task in SUPPORTED_TASK_TYPES:
            req = InferenceRequest(
                model_id=1,
                task_type=task,
                question="What is an FD?",
            )
            self.assertEqual(req.task_type, task)

    def test_inference_service_rejects_unsupported_task_type(self):
        """InferenceService.predict must validate task_type and reject invalid types before MLClient call."""
        mock_db = MagicMock()
        service = InferenceService(mock_db)

        with self.assertRaises(ValueError) as ctx:
            service.predict(
                model_id=1,
                task_type="invalid_custom_task",
                question="What is the credit card interest rate?",
            )
        self.assertIn("The selected task type 'invalid_custom_task' is not supported", str(ctx.exception))

    @patch("app.clients.ml_client.httpx.Client")
    def test_ml_client_propagates_request_id_and_headers(self, mock_client_cls):
        """MLClient must pass X-Request-ID and authentication headers to ML service."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model_id": 1,
            "response": "Test answer",
            "fine_tuned": True,
        }
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = MLClient.predict(
            model_id=1,
            task_type="customer_faq_qa",
            question="How to open account?",
            request_id="trace-abc-123",
        )

        self.assertEqual(result["response"], "Test answer")
        called_args, called_kwargs = mock_client.post.call_args
        headers = called_kwargs.get("headers", {})
        self.assertEqual(headers.get("X-Request-ID"), "trace-abc-123")
        self.assertIn("X-ML-Service-Key", headers)

    @patch("app.clients.ml_client.httpx.Client")
    def test_ml_client_does_not_retry_client_validation_error(self, mock_client_cls):
        """MLClient must NOT retry 400 Bad Request / UnsupportedTaskError."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"detail": "Unsupported task_type 'inference'"}
        import httpx
        from fastapi import HTTPException

        http_error = httpx.HTTPStatusError(
            message="400 Bad Request",
            request=MagicMock(),
            response=mock_resp,
        )
        mock_resp.raise_for_status.side_effect = http_error
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            MLClient.predict(
                model_id=1,
                task_type="customer_faq_qa",
                question="How to open account?",
                request_id="trace-test-400",
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Unsupported task_type 'inference'", ctx.exception.detail)
        # Verify it was only called once, NOT retried
        self.assertEqual(mock_client.post.call_count, 1)

    @patch("app.clients.ml_client.time.sleep")
    @patch("app.clients.ml_client.httpx.Client")
    def test_ml_client_retries_transient_429_with_backoff(self, mock_client_cls, mock_sleep):
        """MLClient must retry 429 up to 3 attempts and respect Retry-After."""
        mock_client = MagicMock()
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {"Retry-After": "2"}

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = {"response": "Success after retry"}

        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = [mock_resp_429, mock_resp_200]
        mock_client_cls.return_value = mock_client

        result = MLClient.predict(
            model_id=1,
            task_type="customer_faq_qa",
            question="How to open account?",
            request_id="trace-test-retry",
        )

        self.assertEqual(result["response"], "Success after retry")
        self.assertEqual(mock_client.post.call_count, 2)
        mock_sleep.assert_called_once_with(2.0)


if __name__ == "__main__":
    unittest.main()
