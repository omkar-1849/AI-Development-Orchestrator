from dataclasses import dataclass


@dataclass
class WorkerTask:
    task_id: str
    objective: str
    instructions: list[str]
    files_allowed: list[str]
    acceptance_criteria: list[str]