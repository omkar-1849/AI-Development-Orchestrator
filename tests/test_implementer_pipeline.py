from src.worker.worker_task import WorkerTask

from src.implementer.implementer_session import ImplementerSession
from src.implementer.implementer_manager import ImplementerManager
from src.implementer.antigravity_adapter import AntigravityAdapter

from src.automation.antigravity_automation import AntigravityAutomation


def test_implementer_pipeline():

    # Create sample worker task
    worker_task = WorkerTask(
        task_id="TASK-001",
        objective="Create a simple Python Hello World program",
        instructions=[
            "Create main.py",
            "Print Hello World when executed"
        ],
        files_allowed=[
            "main.py"
        ],
        acceptance_criteria=[
            "main.py exists",
            "Running the file prints Hello World"
        ]
    )

    # Create Antigravity automation
    automation = AntigravityAutomation()

    # Connect automation to adapter
    implementer = AntigravityAdapter(
        automation=automation
    )

    # Create project session
    session = ImplementerSession(
        project_name="TestProject"
    )

    # Create manager
    manager = ImplementerManager(
        implementer=implementer,
        session=session
    )

    # Execute task
    result = manager.execute_task(
        worker_task
    )

    print("\n--- IMPLEMENTER RESULT ---\n")
    print(result)


if __name__ == "__main__":
    test_implementer_pipeline()