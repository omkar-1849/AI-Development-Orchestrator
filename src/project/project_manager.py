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


def get_default_workspace_base_dir() -> Path:
    """
    Dynamically resolve the default workspace base directory for the current user.

    Prefers ~/Desktop/AIProjects if the Desktop directory exists;
    otherwise falls back to ~/AIProjects.
    """
    home = Path.home()
    desktop = home / "Desktop"
    if desktop.exists():
        return desktop / "AIProjects"
    return home / "AIProjects"


def create_project_workspace(
    project_name: str,
    base_path: str | Path | None = None,
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

    if base_path is None:
        base_directory = get_default_workspace_base_dir()
    else:
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