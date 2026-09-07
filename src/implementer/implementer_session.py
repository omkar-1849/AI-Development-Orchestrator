from dataclasses import dataclass


@dataclass
class ImplementerSession:
    project_name: str
    project_path: str
    initialized: bool = False