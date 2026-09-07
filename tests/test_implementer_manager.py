import unittest

from src.implementer.mock_implementer import MockImplementer
from src.implementer.implementer_session import ImplementerSession
from src.implementer.implementer_manager import ImplementerManager
from src.implementer.implementer_result import ImplementerResult
from src.state.phase_state import PhaseState
from src.worker.worker_task import WorkerTask


class TestImplementerManager(unittest.TestCase):

    def _make_manager(self):
        implementer = MockImplementer()
        session = ImplementerSession(
            project_name="TestProject",
            project_path="/tmp/test-project",
        )
        phase_state = PhaseState(
            project_name="TestProject",
        )
        manager = ImplementerManager(
            implementer=implementer,
            session=session,
            phase_state=phase_state,
        )
        return manager

    def _make_worker_task(self, task_id="TASK-001"):
        return WorkerTask(
            task_id=task_id,
            objective="Create the backend structure",
            instructions=["Create main.py"],
            files_allowed=["main.py"],
            acceptance_criteria=["main.py exists"],
        )

    def test_execute_task_returns_implementer_result(self):
        manager = self._make_manager()
        task = self._make_worker_task()
        result = manager.execute_task(task)
        self.assertIsInstance(result, ImplementerResult)

    def test_execute_task_returns_success(self):
        manager = self._make_manager()
        task = self._make_worker_task()
        result = manager.execute_task(task)
        self.assertTrue(result.success)

    def test_first_task_uses_initial_prompt(self):
        manager = self._make_manager()
        self.assertFalse(manager.session.initialized)
        task = self._make_worker_task()
        manager.execute_task(task)
        self.assertTrue(manager.session.initialized)

    def test_second_task_uses_task_prompt(self):
        manager = self._make_manager()
        task1 = self._make_worker_task("TASK-001")
        task2 = self._make_worker_task("TASK-002")
        manager.execute_task(task1)
        self.assertTrue(manager.session.initialized)
        result = manager.execute_task(task2)
        self.assertTrue(result.success)

    def test_execute_multiple_tasks(self):
        manager = self._make_manager()
        for i in range(3):
            task = self._make_worker_task(f"TASK-{i:03d}")
            result = manager.execute_task(task)
            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()