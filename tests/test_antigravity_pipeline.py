import unittest
from unittest.mock import MagicMock

from src.worker.worker_task import WorkerTask
from src.implementer.implementer_manager import ImplementerManager
from src.implementer.implementer_session import ImplementerSession
from src.implementer.implementer_result import ImplementerResult
from src.implementer.antigravity_adapter import AntigravityAdapter
from src.automation.mock_automation import MockAutomation
from src.state.phase_state import PhaseState


class TestAntigravityPipeline(unittest.TestCase):
    """Test the Antigravity implementer pipeline using MockAutomation."""

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

    def _make_task(self, task_id="test-001", objective="Reply with HI only"):
        return WorkerTask(
            task_id=task_id,
            objective=objective,
            instructions=["Reply with exactly: HI"],
            files_allowed=[],
            acceptance_criteria=["Response must be exactly HI"],
        )

    def test_single_task_execution(self):
        manager = self._make_pipeline()
        task = self._make_task()
        result = manager.execute_task(task)
        self.assertIsInstance(result, ImplementerResult)
        self.assertTrue(result.success)

    def test_multiple_task_execution(self):
        manager = self._make_pipeline()

        task_1 = self._make_task("test-001", "Reply with HI only")
        result_1 = manager.execute_task(task_1)
        self.assertTrue(result_1.success)

        task_2 = self._make_task(
            "test-002",
            "Add a greeting function to the existing main.py",
        )
        result_2 = manager.execute_task(task_2)
        self.assertTrue(result_2.success)

    def test_session_initialized_after_first_task(self):
        manager = self._make_pipeline()
        self.assertFalse(manager.session.initialized)

        task = self._make_task()
        manager.execute_task(task)
        self.assertTrue(manager.session.initialized)

    def test_result_has_output(self):
        manager = self._make_pipeline()
        task = self._make_task()
        result = manager.execute_task(task)
        self.assertIsNotNone(result.output)


if __name__ == "__main__":
    unittest.main()