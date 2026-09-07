import unittest

from src.implementer.prompt_builder import ImplementerPromptBuilder
from src.implementer.implementer_manager import ImplementerManager
from src.implementer.implementer_session import ImplementerSession
from src.implementer.mock_implementer import MockImplementer
from src.state.phase_state import PhaseState
from src.worker.worker_task import WorkerTask


class TestRetryFeedback(unittest.TestCase):

    def _make_worker_task(self):
        return WorkerTask(
            task_id="TASK-001",
            objective="Create a REST API",
            instructions=["Create main.py", "Add GET endpoint"],
            files_allowed=["main.py"],
            acceptance_criteria=["GET /api returns 200"],
        )

    def test_first_attempt_no_correction_section(self):
        """First attempt prompt should not contain retry feedback."""
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_task_prompt(
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertNotIn("PREVIOUS REVIEW FEEDBACK", prompt)
        self.assertNotIn("retry attempt", prompt.lower())

    def test_initial_prompt_no_correction_section(self):
        """Initial prompt should not contain retry feedback."""
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/tmp/test",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertNotIn("PREVIOUS REVIEW FEEDBACK", prompt)

    def test_retry_prompt_includes_reviewer_issues(self):
        """Retry prompt should include reviewer feedback issues."""
        task = self._make_worker_task()
        feedback = [
            "Missing error handling in GET endpoint",
            "No input validation",
        ]
        prompt = ImplementerPromptBuilder.build_retry_prompt(
            task,
            "reports/phase_1_attempt_2.md",
            retry_feedback=feedback,
            attempt_number=2,
        )
        self.assertIn("PREVIOUS REVIEW FEEDBACK", prompt)
        self.assertIn("Missing error handling in GET endpoint", prompt)
        self.assertIn("No input validation", prompt)

    def test_retry_prompt_includes_attempt_number(self):
        """Retry prompt should include the attempt number."""
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_retry_prompt(
            task,
            "reports/phase_1_attempt_3.md",
            retry_feedback=["Fix tests"],
            attempt_number=3,
        )
        self.assertIn("retry attempt 3", prompt.lower())

    def test_retry_prompt_multiple_issues_formatted(self):
        """Multiple issues should be numbered."""
        task = self._make_worker_task()
        feedback = [
            "Issue one",
            "Issue two",
            "Issue three",
        ]
        prompt = ImplementerPromptBuilder.build_retry_prompt(
            task,
            "reports/phase_1_attempt_2.md",
            retry_feedback=feedback,
            attempt_number=2,
        )
        self.assertIn("1. Issue one", prompt)
        self.assertIn("2. Issue two", prompt)
        self.assertIn("3. Issue three", prompt)

    def test_retry_prompt_empty_issues_handled(self):
        """Empty issue list should not crash."""
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_retry_prompt(
            task,
            "reports/phase_1_attempt_2.md",
            retry_feedback=[],
            attempt_number=2,
        )
        # Should still contain the task but no PREVIOUS REVIEW FEEDBACK
        self.assertIn("TASK-001", prompt)
        self.assertNotIn("PREVIOUS REVIEW FEEDBACK", prompt)

    def test_retry_prompt_none_feedback_handled(self):
        """None feedback should not crash."""
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_retry_prompt(
            task,
            "reports/phase_1_attempt_2.md",
            retry_feedback=None,
            attempt_number=2,
        )
        self.assertIn("TASK-001", prompt)
        self.assertNotIn("PREVIOUS REVIEW FEEDBACK", prompt)

    def test_retry_prompt_still_contains_task_details(self):
        """Retry prompt should still include original task details."""
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_retry_prompt(
            task,
            "reports/phase_1_attempt_2.md",
            retry_feedback=["Fix the API"],
            attempt_number=2,
        )
        self.assertIn("TASK-001", prompt)
        self.assertIn("Create a REST API", prompt)
        self.assertIn("Create main.py", prompt)
        self.assertIn("GET /api returns 200", prompt)
        self.assertIn("reports/phase_1_attempt_2.md", prompt)

    def test_manager_uses_retry_prompt_when_feedback_provided(self):
        """ImplementerManager should use retry prompt when feedback is given."""
        implementer = MockImplementer()
        session = ImplementerSession(
            project_name="TestProject",
            project_path="/tmp/test",
        )
        phase_state = PhaseState(project_name="TestProject")
        manager = ImplementerManager(
            implementer=implementer,
            session=session,
            phase_state=phase_state,
        )
        task = self._make_worker_task()

        # First call initializes session
        manager.execute_task(task)
        self.assertTrue(session.initialized)

        # Second call with feedback should succeed
        result = manager.execute_task(
            task,
            retry_feedback=["Fix error handling"],
            attempt_number=2,
        )
        self.assertTrue(result.success)

    def test_manager_no_feedback_uses_task_prompt(self):
        """Manager without feedback uses normal task prompt."""
        implementer = MockImplementer()
        session = ImplementerSession(
            project_name="TestProject",
            project_path="/tmp/test",
        )
        phase_state = PhaseState(project_name="TestProject")
        manager = ImplementerManager(
            implementer=implementer,
            session=session,
            phase_state=phase_state,
        )
        task = self._make_worker_task()

        # First call (initial prompt)
        manager.execute_task(task)

        # Second call without feedback
        result = manager.execute_task(task)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
