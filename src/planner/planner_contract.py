from dataclasses import dataclass, field
from typing import List


@dataclass
class PlannerTask:
    """
    Standard contract between the Planner AI
    and the Orchestrator.
    """

    task_id: str
    status: str
    objective: str

    instructions: List[str] = field(
        default_factory=list
    )

    files_allowed: List[str] = field(
        default_factory=list
    )

    acceptance_criteria: List[str] = field(
        default_factory=list
    )