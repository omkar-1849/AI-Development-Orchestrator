from src.worker.worker_task import WorkerTask


def dispatch_next_phase(
    next_phase,
    phase_number
):
    """
    Convert a Reviewer next_phase definition
    into a WorkerTask.
    """

    worker_task = WorkerTask(
        task_id=f"PHASE-{phase_number}",
        objective=next_phase["objective"],
        instructions=next_phase["instructions"],
        files_allowed=next_phase["files_allowed"],
        acceptance_criteria=(
            next_phase["acceptance_criteria"]
        ),
    )

    print("\n--- NEXT PHASE DISPATCHED ---\n")
    print("Task ID:", worker_task.task_id)
    print("Objective:", worker_task.objective)

    return worker_task
