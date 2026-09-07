import unittest

from src.worker.worker_task import WorkerTask
from src.worker.worker_prompt import build_worker_prompt


class TestLegacyWorkerPrompt(unittest.TestCase):

    def test_build_worker_prompt(self):
        worker_task = WorkerTask(
            task_id="TASK-001",
            objective="Create a Python calculator module",
            instructions=[
                "Create calculator.py",
                "Implement addition",
                "Implement subtraction",
                "Implement multiplication",
                "Implement division with division by zero handling",
            ],
            files_allowed=[
                "calculator.py",
                "test_calculator.py",
            ],
            acceptance_criteria=[
                "All arithmetic operations work correctly",
                "Division by zero is handled",
                "Functions can be imported",
            ],
        )

        prompt = build_worker_prompt(worker_task)

        self.assertIn("TASK ID:\nTASK-001", prompt)
        self.assertIn("Create a Python calculator module", prompt)
        self.assertIn("Create calculator.py", prompt)
        self.assertIn("calculator.py", prompt)
        self.assertIn("Division by zero is handled", prompt)
        self.assertIn("implementation_summary", prompt)


if __name__ == "__main__":
    unittest.main()