from src.worker.worker_task import WorkerTask
from src.worker.worker_prompt import build_worker_prompt


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

print("\n--- GENERATED WORKER PROMPT ---\n")
print(prompt)