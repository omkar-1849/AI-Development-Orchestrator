from dataclasses import dataclass


@dataclass
class WorkerResponse:
    implementation_summary: str
    files_modified: list[str]
    changes_made: list[str]
    acceptance_check: list[str]
    blockers: str