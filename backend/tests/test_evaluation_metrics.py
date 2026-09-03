import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.evaluation_adapter.evaluation_adapter import _compute_token_metrics, _tokenize
from app.model.evaluation_run_model import Evaluation_Model
from app.services.evaluation_service.evaluation_service import _enrich_evaluation, get_evaluation_detail


class TestEvaluationMetrics(unittest.TestCase):
    def test_token_metrics_exact_match(self):
        prec, rec, f1 = _compute_token_metrics("HDFC Bank Mobile App", "HDFC Bank Mobile App")
        self.assertEqual(prec, 1.0)
        self.assertEqual(rec, 1.0)
        self.assertEqual(f1, 1.0)

    def test_token_metrics_partial_overlap(self):
        prec, rec, f1 = _compute_token_metrics("Yes, I can help you with queries", "Sure how can i help you")
        self.assertGreater(prec, 0.0)
        self.assertGreater(rec, 0.0)
        self.assertGreater(f1, 0.0)

    def test_token_metrics_disjoint(self):
        prec, rec, f1 = _compute_token_metrics("Hello world", "Goodbye moon")
        self.assertEqual(prec, 0.0)
        self.assertEqual(rec, 0.0)
        self.assertEqual(f1, 0.0)

    def test_enrich_evaluation_computes_score_from_metrics(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        eval_item = Evaluation_Model(
            evaluation_id=1,
            run_id=1,
            model_id=1,
            test_dataset_id=1,
            evaluation_status="COMPLETED",
            answer_accuracy=0.852,
            intent_structured_accuracy=0.800,
            policy_flag_accuracy=0.900,
            full_structured_match=0.780,
            created_at=datetime.now(timezone.utc),
        )

        enriched = _enrich_evaluation(mock_db, eval_item)
        self.assertEqual(enriched.display_id, "EV-001")
        self.assertEqual(enriched.score_value, 85.2)
        self.assertEqual(enriched.score, "85.2%")

    def test_get_evaluation_detail_generates_complete_metrics_and_breakdown(self):
        mock_db = MagicMock()
        eval_item = Evaluation_Model(
            evaluation_id=1,
            run_id=1,
            model_id=1,
            test_dataset_id=1,
            evaluation_status="COMPLETED",
            answer_accuracy=0.85,
            intent_structured_accuracy=0.80,
            policy_flag_accuracy=0.90,
            full_structured_match=0.75,
            average_latency_seconds=1.25,
            total_examples=5,
            critical_safety_failures=0,
            created_at=datetime.now(timezone.utc),
        )

        def mock_query(model_cls):
            mock_q = MagicMock()
            if model_cls == Evaluation_Model:
                mock_q.filter.return_value.first.return_value = eval_item
            else:
                mock_q.filter.return_value.first.return_value = None
            return mock_q

        mock_db.query.side_effect = mock_query

        detail = get_evaluation_detail(mock_db, 1)
        self.assertIsNotNone(detail["overall_score"])
        self.assertEqual(detail["overall_score"], 85.0)
        self.assertEqual(detail["overall_score_str"], "85.0%")
        self.assertEqual(detail["accuracy"], 85.0)
        self.assertEqual(detail["precision"], 80.0)
        self.assertEqual(detail["recall"], 90.0)
        self.assertEqual(detail["status"], "completed")
        self.assertTrue(detail["target_met"])
        self.assertEqual(detail["threshold"], 70.0)

    def test_get_evaluation_detail_below_threshold_is_completed_not_failed(self):
        mock_db = MagicMock()
        eval_item = Evaluation_Model(
            evaluation_id=2,
            run_id=1,
            model_id=1,
            test_dataset_id=1,
            evaluation_status="COMPLETED",
            answer_accuracy=0.65,
            intent_structured_accuracy=0.65,
            policy_flag_accuracy=0.65,
            full_structured_match=0.65,
            average_latency_seconds=1.2,
            total_examples=10,
            critical_safety_failures=0,
            created_at=datetime.now(timezone.utc),
        )

        def mock_query(model_cls):
            mock_q = MagicMock()
            if model_cls == Evaluation_Model:
                mock_q.filter.return_value.first.return_value = eval_item
            else:
                mock_q.filter.return_value.first.return_value = None
            return mock_q

        mock_db.query.side_effect = mock_query

        detail = get_evaluation_detail(mock_db, 2)
        self.assertEqual(detail["status"], "completed")
        self.assertEqual(detail["overall_score"], 65.0)
        self.assertFalse(detail["target_met"])
        self.assertEqual(detail["threshold"], 70.0)

    def test_get_evaluation_detail_technical_crash_is_failed(self):
        mock_db = MagicMock()
        eval_item = Evaluation_Model(
            evaluation_id=3,
            run_id=1,
            model_id=1,
            test_dataset_id=1,
            evaluation_status="FAILED",
            error_message="Runtime out of memory error during inference worker",
            created_at=datetime.now(timezone.utc),
        )

        def mock_query(model_cls):
            mock_q = MagicMock()
            if model_cls == Evaluation_Model:
                mock_q.filter.return_value.first.return_value = eval_item
            else:
                mock_q.filter.return_value.first.return_value = None
            return mock_q

        mock_db.query.side_effect = mock_query

        detail = get_evaluation_detail(mock_db, 3)
        self.assertEqual(detail["status"], "failed")


if __name__ == "__main__":
    unittest.main()
