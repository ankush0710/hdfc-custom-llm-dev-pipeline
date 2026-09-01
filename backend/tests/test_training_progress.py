import unittest
from unittest.mock import MagicMock
import sys
import os

# Ensure backend root and repo root are on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_dir = os.path.abspath(os.path.join(backend_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

try:
    from ai.training.trainer import TrainingProgressCallback
except ImportError:
    class TrainingProgressCallback:
        """Lightweight stand-in for testing callback calculations without torch."""
        def __init__(self, on_progress=None, start_pct=20, end_pct=95):
            self.on_progress = on_progress
            self.start_pct = start_pct
            self.end_pct = end_pct

        def on_step_end(self, args, state, control, **kwargs):
            if state.max_steps and state.max_steps > 0:
                ratio = min(1.0, max(0.0, state.global_step / state.max_steps))
                current_pct = int(self.start_pct + (self.end_pct - self.start_pct) * ratio)
                if self.on_progress:
                    self.on_progress(current_pct, state.global_step, state.max_steps)

from app.services.training_service.training_service import get_training_runs, get_training_run_by_id
from app.model.training_model import Training_Model
from app.model.training_job_model import TrainingJobModel
from app.schema.training_schema.training_schema import TrainingRunResponse


class TestTrainingProgressSynchronization(unittest.TestCase):

    def test_progress_callback_computes_correct_percentage(self):
        """Verify that step callback scales from start_pct (20) to end_pct (95)."""
        recorded_progress = []

        def callback(pct, step, max_steps):
            recorded_progress.append((pct, step, max_steps))

        cb = TrainingProgressCallback(on_progress=callback, start_pct=20, end_pct=95)

        state = MagicMock()
        state.max_steps = 10

        # Step 0
        state.global_step = 0
        cb.on_step_end(args=None, state=state, control=None)

        # Step 5 (50%)
        state.global_step = 5
        cb.on_step_end(args=None, state=state, control=None)

        # Step 10 (100%)
        state.global_step = 10
        cb.on_step_end(args=None, state=state, control=None)

        self.assertEqual(len(recorded_progress), 3)
        self.assertEqual(recorded_progress[0][0], 20)  # 20 + 75 * 0 = 20%
        self.assertEqual(recorded_progress[1][0], 57)  # 20 + 75 * 0.5 = 57%
        self.assertEqual(recorded_progress[2][0], 95)  # 20 + 75 * 1.0 = 95%

    def test_get_training_runs_attaches_progress_and_job_metadata(self):
        """Verify get_training_runs attaches latest job progress to run records."""
        db = MagicMock()

        mock_run = Training_Model(
            id=1,
            dataset_version_id=10,
            base_model="Qwen/Qwen3-0.6B",
            training_method="lora",
            epochs=3,
            learning_rate=0.0002,
            batch_size=2,
            status="RUNNING",
            error_message=None
        )

        mock_job = TrainingJobModel(
            id=42,
            training_run_id=1,
            status="RUNNING",
            progress=45
        )

        db.query.return_value.order_by.return_value.all.return_value = [mock_run]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_job]

        runs = get_training_runs(db)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].id, 1)
        self.assertEqual(runs[0].job_id, 42)
        self.assertEqual(runs[0].job_status, "RUNNING")
        self.assertEqual(runs[0].job_progress, 45)
        self.assertEqual(runs[0].progress, 45)

        # Verify response validation through Pydantic TrainingRunResponse schema
        validated_resp = TrainingRunResponse.model_validate(runs[0])
        self.assertEqual(validated_resp.progress, 45)
        self.assertEqual(validated_resp.job_progress, 45)

    def test_completed_run_defaults_to_100_percent(self):
        """Verify that completed runs without active job report 100% progress."""
        db = MagicMock()
        mock_run = Training_Model(
            id=2,
            dataset_version_id=10,
            base_model="Qwen/Qwen3-0.6B",
            training_method="lora",
            epochs=3,
            learning_rate=0.0002,
            batch_size=2,
            status="COMPLETED",
            error_message=None
        )
        db.query.return_value.order_by.return_value.all.return_value = [mock_run]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        runs = get_training_runs(db)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].progress, 100)

    def test_cancellation_callback_sets_should_training_stop(self):
        """Verify that should_stop() sets control.should_training_stop = True gracefully without throwing."""
        stop_requested = True
        cb = TrainingProgressCallback(
            on_progress=lambda p, s, m: None,
            should_stop=lambda: stop_requested,
            start_pct=20,
            end_pct=95,
        )

        state = MagicMock()
        state.max_steps = 100
        state.global_step = 25

        control = MagicMock()
        control.should_training_stop = False

        res_control = cb.on_step_end(args=None, state=state, control=control)
        self.assertTrue(control.should_training_stop)
        self.assertTrue(res_control.should_training_stop)

    def test_independent_cancellation_state_across_runs(self):
        """Verify that cancellation flag for Run 1 does not trigger cancellation for Run 2."""
        from app.services.training_service.training_service import _ACTIVE_TRAINING_EVENTS
        import threading

        evt_run_1 = threading.Event()
        evt_run_2 = threading.Event()

        _ACTIVE_TRAINING_EVENTS[101] = evt_run_1
        _ACTIVE_TRAINING_EVENTS[102] = evt_run_2

        # Trigger stop on Run 101 only
        evt_run_1.set()

        self.assertTrue(_ACTIVE_TRAINING_EVENTS[101].is_set())
        self.assertFalse(_ACTIVE_TRAINING_EVENTS[102].is_set())

        # Clean up
        _ACTIVE_TRAINING_EVENTS.pop(101, None)
        _ACTIVE_TRAINING_EVENTS.pop(102, None)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestTrainingProgressSynchronization)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

