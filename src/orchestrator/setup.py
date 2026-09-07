from dataclasses import dataclass
from typing import Callable, Optional

from src.memory.database import initialize_database
from src.state.state_manager import StateManager
from src.state.phase_state import PhaseState
from src.input import collect_requirements
from src.orchestrator.events import EventCallback, EventType, emit_event

from src.project.project_manager import (
    collect_project_name,
    create_project_workspace,
)


@dataclass
class OrchestratorSetup:
    workflow: StateManager
    phase_state: PhaseState
    user_request: str
    project_name: str
    project_path: str


def setup_orchestrator(
    project_name: Optional[str] = None,
    project_path: Optional[str] = None,
    requirement_collector: Optional[Callable[[], str]] = None,
    project_name_collector: Optional[Callable[[], str]] = None,
    user_requirements: Optional[str] = None,
    event_callback: Optional[EventCallback] = None,
) -> OrchestratorSetup:
    """
    Initialize runtime environment, database, workflow state,
    phase state, and collect initial project requirements.

    Args:
        project_name: Name of the project. If None, collected interactively.
        project_path: Filesystem path to the project directory.
                      If None, a workspace is created dynamically.
        requirement_collector: Optional custom callable to collect requirements.
                               Defaults to collect_requirements (CLI).
        project_name_collector: Optional custom callable to collect the project name.
                                Defaults to collect_project_name (CLI).
        user_requirements: Optional direct string of user requirements.
                           If provided, bypasses requirement_collector and CLI prompts.
        event_callback: Optional callback receiving OrchestratorEvent instances.

    Returns:
        OrchestratorSetup: Initialized setup context.
    """

    emit_event(
        event_callback,
        EventType.PROJECT_SETUP_STARTED,
        "Initializing project setup...",
        level="INFO",
    )

    # =========================
    # COLLECT PROJECT NAME
    # =========================

    if project_name is None:

        if project_name_collector is not None:
            project_name = project_name_collector()
        else:
            project_name = collect_project_name()

    # =========================
    # CREATE PROJECT WORKSPACE
    # =========================

    if project_path is None:

        workspace = create_project_workspace(
            project_name
        )

        project_name = workspace.project_name
        project_path = str(workspace.project_path)

        print(
            "\n================================"
        )
        print(
            "PROJECT WORKSPACE CREATED"
        )
        print(
            "================================"
        )
        print(
            "Project Name:", project_name
        )
        print(
            "Project Path:", project_path
        )

    emit_event(
        event_callback,
        EventType.PROJECT_WORKSPACE_CREATED,
        f"Project workspace created at {project_path}",
        level="SUCCESS",
        data={"project_name": project_name, "project_path": project_path},
    )

    # =========================
    # INITIALIZE DATABASE
    # =========================

    initialize_database()

    # =========================
    # INITIALIZE WORKFLOW
    # =========================

    workflow = StateManager()

    # =========================
    # INITIALIZE PHASE STATE
    # =========================

    phase_state = PhaseState(
        project_name=project_name
    )

    print("\n--- INITIAL PHASE STATE ---")
    print("Phase:", phase_state.current_phase)
    print("Attempt:", phase_state.current_attempt)
    print("Report:", phase_state.get_report_path())

    # =========================
    # USER REQUIREMENTS INPUT
    # =========================

    if user_requirements is not None and user_requirements.strip():
        user_request = user_requirements.strip()
    elif requirement_collector is not None:
        user_request = requirement_collector()
    else:
        user_request = collect_requirements()

    print("\n--- USER REQUEST ---\n")
    print(user_request)

    emit_event(
        event_callback,
        EventType.REQUIREMENTS_RECEIVED,
        "Project requirements received",
        level="SUCCESS",
        data={"requirements": user_request},
    )

    return OrchestratorSetup(
        workflow=workflow,
        phase_state=phase_state,
        user_request=user_request,
        project_name=project_name,
        project_path=project_path,
    )

