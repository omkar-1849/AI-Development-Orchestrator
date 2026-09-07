from src.worker.worker_task import WorkerTask
from src.implementer.implementer_manager import ImplementerManager
from src.implementer.implementer_session import ImplementerSession
from src.implementer.antigravity_adapter import AntigravityAdapter
from src.automation.antigravity_automation import AntigravityAutomation


def test_antigravity_pipeline():

    # One session for the whole project
    session = ImplementerSession(
        project_name="TestProject"
    )

    automation = AntigravityAutomation()

    implementer = AntigravityAdapter(
        automation=automation
    )

    manager = ImplementerManager(
        implementer=implementer,
        session=session
    )

    # ---------------- TASK 1 ----------------

    task_1 = WorkerTask(
        task_id="test-001",
        objective="Reply with HI only",
        instructions=[
            "Reply with exactly: HI"
        ],
        files_allowed=[],
        acceptance_criteria=[
            "Response must be exactly HI"
        ]
    )

    print("\n--- EXECUTING TASK 1 ---\n")

    result_1 = manager.execute_task(task_1)

    print(result_1)

    # ---------------- TASK 2 ----------------

    task_2 = WorkerTask(
        task_id="test-002",
        objective="Add a greeting function to the existing main.py",
        instructions=[
            "Continue working in the existing project",
            "Add a function named greet",
            "The function should print Welcome"
        ],
        files_allowed=[
            "main.py"
        ],
        acceptance_criteria=[
            "greet function exists",
            "Calling greet prints Welcome"
        ]
    )

    print("\n--- EXECUTING TASK 2 ---\n")

    result_2 = manager.execute_task(task_2)

    print(result_2)


if __name__ == "__main__":
    test_antigravity_pipeline()