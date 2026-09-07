import unittest

from src.implementer.prompt_builder import ImplementerPromptBuilder
from src.worker.worker_task import WorkerTask


class TestPromptBuilder(unittest.TestCase):

    def _make_worker_task(self):
        return WorkerTask(
            task_id="TASK-001",
            objective="Create a FastAPI backend",
            instructions=[
                "Create main.py",
                "Set up FastAPI app",
            ],
            files_allowed=[
                "main.py",
                "requirements.txt",
            ],
            acceptance_criteria=[
                "FastAPI app starts",
                "main.py exists",
            ],
        )

    def test_build_initial_prompt_contains_project_name(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("TestProject", prompt)

    def test_build_initial_prompt_contains_project_path(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("/path/to/project", prompt)

    def test_build_initial_prompt_contains_task_id(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("TASK-001", prompt)

    def test_build_initial_prompt_contains_objective(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("Create a FastAPI backend", prompt)

    def test_build_initial_prompt_contains_report_path(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("reports/phase_1_attempt_1.md", prompt)

    def test_build_initial_prompt_contains_instructions(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("Create main.py", prompt)
        self.assertIn("Set up FastAPI app", prompt)

    def test_build_initial_prompt_contains_report_end_marker(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_initial_prompt(
            "TestProject",
            "/path/to/project",
            task,
            "reports/phase_1_attempt_1.md",
        )
        self.assertIn("<!-- REPORT_END -->", prompt)

    def test_build_task_prompt_contains_task_id(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_task_prompt(
            task,
            "reports/phase_2_attempt_1.md",
        )
        self.assertIn("TASK-001", prompt)

    def test_build_task_prompt_contains_objective(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_task_prompt(
            task,
            "reports/phase_2_attempt_1.md",
        )
        self.assertIn("Create a FastAPI backend", prompt)

    def test_build_task_prompt_contains_report_path(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_task_prompt(
            task,
            "reports/phase_2_attempt_1.md",
        )
        self.assertIn("reports/phase_2_attempt_1.md", prompt)

    def test_build_task_prompt_contains_acceptance_criteria(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_task_prompt(
            task,
            "reports/phase_2_attempt_1.md",
        )
        self.assertIn("FastAPI app starts", prompt)
        self.assertIn("main.py exists", prompt)

    def test_build_task_prompt_contains_files_allowed(self):
        task = self._make_worker_task()
        prompt = ImplementerPromptBuilder.build_task_prompt(
            task,
            "reports/phase_2_attempt_1.md",
        )
        self.assertIn("main.py", prompt)
        self.assertIn("requirements.txt", prompt)


if __name__ == "__main__":
    unittest.main()