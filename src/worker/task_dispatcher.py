from src.worker.worker_task import WorkerTask


def dispatch_task(planner_task):
    """
    Convert a validated PlannerTask into a WorkerTask.
    """

    worker_task = WorkerTask(
        task_id=planner_task.task_id,
        objective=planner_task.objective,
        instructions=planner_task.instructions,
        files_allowed=planner_task.files_allowed,
        acceptance_criteria=planner_task.acceptance_criteria,
    )

    print("\n--- TASK DISPATCHED TO WORKER ---\n")
    print("Task ID:", worker_task.task_id)
    print("Objective:", worker_task.objective)

    return worker_task