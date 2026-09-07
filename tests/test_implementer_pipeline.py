import unittest
from unittest.mock import MagicMock

from src.worker.worker_task import WorkerTask
from src.implementer.implementer_manager import ImplementerManager
from src.implementer.implementer_session import ImplementerSession
from src.implementer.implementer_result import ImplementerResult
from src.implementer.antigravity_adapter import AntigravityAdapter
from src.automation.mock_automation import MockAutomation
from src.automation.automation_result import AutomationResult
from src.state.phase_state import PhaseState


class TestImplementerPipeline(unittest.TestCase):
    """Test the implementer pipeline using MockAutomation instead of live AntigravityAutomation."""

    def _make_pipeline(self):
        automation = MockAutomation()
        implementer = AntigravityAdapter(automation=automation)
        session = ImplementerSession(
            project_name="TestProject",
            project_path="/tmp/test-project",
        )
        phase_state = PhaseState(project_name="TestProject")
        manager = ImplementerManager(
            implementer=implementer,
            session=session,
            phase_state=phase_state,
        )
        return manager

    def _make_task(self, task_id="TASK-001"):
        return WorkerTask(
            task_id=task_id,
            objective="Create a simple Python Hello World program",
            instructions=[
                "Create main.py",
                "Print Hello World when executed",
            ],
            files_allowed=["main.py"],
            acceptance_criteria=[
                "main.py exists",
                "Running the file prints Hello World",
            ],
        )

    def test_pipeline_returns_implementer_result(self):
        manager = self._make_pipeline()
        task = self._make_task()
        result = manager.execute_task(task)
        self.assertIsInstance(result, ImplementerResult)

    def test_pipeline_success(self):
        manager = self._make_pipeline()
        task = self._make_task()
        result = manager.execute_task(task)
        self.assertTrue(result.success)

    def test_pipeline_output_not_none(self):
        manager = self._make_pipeline()
        task = self._make_task()
        result = manager.execute_task(task)
        self.assertIsNotNone(result.output)

    def test_adapter_handles_mock_automation_result(self):
        """Verify AntigravityAdapter correctly processes MockAutomation AutomationResult."""
        automation = MockAutomation()
        adapter = AntigravityAdapter(automation=automation)
        result = adapter.execute("Test prompt")
        self.assertIsInstance(result, ImplementerResult)
        self.assertTrue(result.success)

    def test_adapter_handles_failed_automation(self):
        """Verify adapter correctly handles a failed AutomationResult."""
        automation = MagicMock()
        automation.execute.return_value = AutomationResult(
            success=False,
            error="Simulated failure",
        )
        adapter = AntigravityAdapter(automation=automation)
        result = adapter.execute("Test prompt")
        self.assertFalse(result.success)
        self.assertIn("failed", result.message.lower())


if __name__ == "__main__":
    unittest.main()