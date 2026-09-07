from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class ProjectWorkspace:
    project_name: str
    project_path: Path
    reports_path: Path


def validate_project_name(project_name: str) -> str:
    """
    Validate and normalize a project name.

    Returns a cleaned project name suitable for
    use as a directory name.
    """

    project_name = project_name.strip()

    if not project_name:
        raise ValueError(
            "Project name cannot be empty"
        )

    # Replace spaces with underscores
    project_name = project_name.replace(
        " ",
        "_"
    )

    # Allow letters, numbers, underscores and hyphens
    if not re.fullmatch(
        r"[A-Za-z0-9_-]+",
        project_name
    ):
        raise ValueError(
            "Project name may only contain "
            "letters, numbers, spaces, "
            "underscores, and hyphens"
        )

    return project_name


def create_project_workspace(
    project_name: str,
    base_path: str = (
        "C:/Users/omkar/Desktop/AIProjects"
    )
) -> ProjectWorkspace:
    """
    Create and initialize a project workspace.

    Structure:

    AIProjects/
    └── ProjectName/
        └── reports/
    """

    project_name = validate_project_name(
        project_name
    )

    base_directory = Path(base_path)

    project_path = (
        base_directory / project_name
    )

    reports_path = (
        project_path / "reports"
    )

    # Create directories safely
    reports_path.mkdir(
        parents=True,
        exist_ok=True
    )

    return ProjectWorkspace(
        project_name=project_name,
        project_path=project_path,
        reports_path=reports_path
    )


def collect_project_name() -> str:
    """
    Collect a project name from the user.
    """

    while True:

        print(
            "\n================================"
        )
        print(
            "AI DEVELOPMENT ORCHESTRATOR"
        )
        print(
            "PROJECT SETUP"
        )
        print(
            "================================"
        )

        project_name = input(
            "\nEnter Project Name: "
        )

        try:

            return validate_project_name(
                project_name
            )

        except ValueError as error:

            print(
                f"\n[ERROR] {error}"
            )