# Legacy Worker Architecture (Claude as Worker)

These modules represent the earlier architecture where Claude was used directly as the Worker agent:
- `worker_executor.py`: Sent worker prompts to Claude and awaited JSON responses.
- `worker_validator.py`: Parsed and validated the Claude JSON worker response.
- `worker_response.py`: Dataclass structure representing Claude's worker response.
- `worker_prompt.py`: Prompt builder instructing Claude to act as the worker.

## Migration Notice
The project has migrated to using **Antigravity** as the Implementer (`src/implementer/` and `src/automation/`), while Claude is retained solely for Planning (`src/planner/`) and Review (`src/reviewer/`).

Active files in `src/worker/` are:
- `worker_task.py`: The `WorkerTask` dataclass used across the entire orchestrator.
- `task_dispatcher.py`: Dispatches initial PlannerTask as WorkerTask.
- `next_phase_dispatcher.py`: Converts Reviewer next_phase instructions into WorkerTask.
