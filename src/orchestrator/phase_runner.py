from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.automation.claude_sender import send_prompt
from src.automation.claude_waiter import wait_for_response
from src.automation.claude_response import capture_latest_response
from src.automation.explorer_automation import select_report_file
from src.implementer.implementer_manager import ImplementerManager
from src.memory.conversation_store import save_interaction
from src.reviewer.report_waiter import wait_for_report
from src.reviewer.review_prompt import build_review_prompt
from src.reviewer.review_validator import validate_review_response
from src.reviewer.review_contract import ReviewResult
from src.state.phase_state import PhaseState
from src.state.state_manager import StateManager
from src.state.workflow_state import WorkflowState
from src.worker.worker_task import WorkerTask
from src.orchestrator.events import EventCallback, EventType, emit_event


@dataclass
class PhaseExecutionResult:
    review_result: ReviewResult
    implementer_interaction_id: int
    implementer_result: Any
    report_content: str


def run_phase(
    worker_task: WorkerTask,
    phase_state: PhaseState,
    workflow: StateManager,
    manager: ImplementerManager,
    claude: Any,
    project_name: str,
    project_path: str,
    event_callback: Optional[EventCallback] = None,
    retry_feedback: Optional[list] = None,
    attempt_number: int = 1,
) -> PhaseExecutionResult:
    """
    Execute one complete implementation -> report waiting -> review cycle.

    Args:
        worker_task: The task to be implemented in this phase.
        phase_state: Tracking object for current phase, attempt, and report paths.
        workflow: Workflow state manager.
        manager: ImplementerManager for dispatching task to Antigravity.
        claude: Reference to the Claude browser/UI automation window.
        project_name: Name of the current project.
        project_path: Filesystem path to the project root.
        event_callback: Optional callback for orchestrator events.
        retry_feedback: Optional list of reviewer issues from a previous attempt.
        attempt_number: Current attempt number for this phase.

    Returns:
        PhaseExecutionResult: The validated review result and execution artifacts.
    """

    # =========================
    # REMOVE OLD REPORT
    # =========================

    report_file = (
        Path(project_path)
        / phase_state.get_report_path()
    )

    if report_file.exists():

        print(
            f"\nRemoving old report:"
            f"\n{report_file}"
        )

        report_file.unlink()

        print(
            "Old report removed."
        )

    else:

        print(
            "\nNo previous report found."
        )

    # =========================
    # EXECUTE IMPLEMENTATION
    # =========================

    print(
        "\nSending WorkerTask "
        "to Antigravity..."
    )

    emit_event(
        event_callback,
        EventType.IMPLEMENTATION_STARTED,
        f"Task {worker_task.task_id} dispatched to Antigravity ({worker_task.objective})",
        phase=phase_state.current_phase,
        attempt=phase_state.current_attempt,
        level="INFO",
        data={"task_id": worker_task.task_id, "objective": worker_task.objective},
    )

    implementer_result = manager.execute_task(
        worker_task,
        retry_feedback=retry_feedback,
        attempt_number=attempt_number,
    )

    # =========================
    # CHECK IMPLEMENTATION RESULT
    # =========================

    print(
        "\n--- IMPLEMENTER RESULT ---\n"
    )

    print(
        implementer_result
    )

    if not implementer_result.success:
        err_msg = implementer_result.error or implementer_result.message
        emit_event(
            event_callback,
            EventType.PROJECT_FAILED,
            f"Implementation failed: {err_msg}",
            phase=phase_state.current_phase,
            attempt=phase_state.current_attempt,
            level="ERROR",
            data={"error": err_msg},
        )
        raise RuntimeError(err_msg)

    emit_event(
        event_callback,
        EventType.IMPLEMENTATION_COMPLETED,
        "Antigravity implementation step completed",
        phase=phase_state.current_phase,
        attempt=phase_state.current_attempt,
        level="SUCCESS",
    )

    # =========================
    # STORE IMPLEMENTER INTERACTION
    # =========================

    print(
        "\nSaving Implementer interaction..."
    )

    implementer_interaction_id = (
        save_interaction(
            agent="implementer",
            model="Antigravity",
            prompt=(
                f"WorkerTask "
                f"{worker_task.task_id} "
                f"dispatched to Antigravity. "
                f"Expected report: "
                f"{phase_state.get_report_path()}"
            ),
            response=implementer_result.output,
            status="dispatched",
            project_name=project_name,
            phase=phase_state.current_phase,
            attempt=phase_state.current_attempt,
        )
    )

    # =========================
    # WAIT FOR REPORT
    # =========================

    print(
        "\n================================"
    )
    print(
        "WAITING FOR IMPLEMENTATION REPORT"
    )
    print(
        "================================"
    )

    emit_event(
        event_callback,
        EventType.REPORT_WAITING,
        f"Waiting for implementation report ({phase_state.get_report_path()})...",
        phase=phase_state.current_phase,
        attempt=phase_state.current_attempt,
        level="INFO",
        data={"report_path": phase_state.get_report_path()},
    )

    report_content = wait_for_report(
        project_path=project_path,
        report_path=phase_state.get_report_path()
    )

    print(
        "\n--- IMPLEMENTATION REPORT RECEIVED ---\n"
    )

    print(
        report_content
    )

    emit_event(
        event_callback,
        EventType.REPORT_RECEIVED,
        f"Implementation report detected for Phase {phase_state.current_phase} Attempt {phase_state.current_attempt}",
        phase=phase_state.current_phase,
        attempt=phase_state.current_attempt,
        level="SUCCESS",
        data={"report_path": phase_state.get_report_path()},
    )

    # =========================
    # VISUAL REPORT SELECTION (EXPLORER)
    # =========================

    try:
        select_report_file(
            project_path=project_path,
            report_path=phase_state.get_report_path(),
        )
        emit_event(
            event_callback,
            EventType.EXPLORER_REPORT_SELECTED,
            f"Explorer selected report file: {phase_state.get_report_path()}",
            phase=phase_state.current_phase,
            attempt=phase_state.current_attempt,
            level="INFO",
            data={"report_path": phase_state.get_report_path()},
        )
    except Exception as explorer_err:
        print(f"[WARN] Explorer report selection warning: {explorer_err}")

    # =========================
    # BUILD REVIEWER PROMPT
    # =========================

    print(
        "\nBuilding Reviewer prompt..."
    )

    review_prompt = build_review_prompt(
        project_name=project_name,
        phase_state=phase_state,
        report_content=report_content
    )

    # =========================
    # SEND TO REVIEWER
    # =========================

    print(
        "\nSending implementation report "
        "to Claude Reviewer..."
    )

    emit_event(
        event_callback,
        EventType.REVIEW_STARTED,
        "Evaluating implementation report with Reviewer...",
        phase=phase_state.current_phase,
        attempt=phase_state.current_attempt,
        level="INFO",
    )

    send_prompt(
        claude,
        review_prompt
    )

    workflow.transition(
        WorkflowState.WAITING_FOR_RESPONSE
    )

    # =========================
    # WAIT FOR REVIEW
    # =========================

    print(
        "\nWaiting for Reviewer response..."
    )

    wait_for_response(
        claude
    )

    workflow.transition(
        WorkflowState.RESPONSE_RECEIVED
    )

    # =========================
    # CAPTURE REVIEW RESPONSE
    # =========================

    print(
        "\nCapturing Reviewer response..."
    )

    review_response = (
        capture_latest_response(
            claude
        )
    )

    if not review_response:
        raise RuntimeError(
            "Failed to capture "
            "Claude review response"
        )

    print(
        "\n--- RAW REVIEW RESPONSE ---\n"
    )

    print(
        review_response
    )

    emit_event(
        event_callback,
        EventType.REVIEW_RESPONSE_RECEIVED,
        "Reviewer response captured",
        phase=phase_state.current_phase,
        attempt=phase_state.current_attempt,
        level="INFO",
    )

    # =========================
    # VALIDATE REVIEW RESPONSE
    # =========================

    print(
        "\nValidating Reviewer response..."
    )

    review_result = (
        validate_review_response(
            review_response
        )
    )

    if review_result.decision == "APPROVED":
        emit_event(
            event_callback,
            EventType.REVIEW_APPROVED,
            f"Phase {phase_state.current_phase} APPROVED: {review_result.summary}",
            phase=phase_state.current_phase,
            attempt=phase_state.current_attempt,
            level="SUCCESS",
            data={
                "decision": review_result.decision,
                "summary": review_result.summary,
                "next_action": review_result.next_action,
            },
        )
    else:
        emit_event(
            event_callback,
            EventType.REVIEW_REJECTED,
            f"Review decision: {review_result.decision} ({review_result.next_action}): {review_result.summary}",
            phase=phase_state.current_phase,
            attempt=phase_state.current_attempt,
            level="WARNING",
            data={
                "decision": review_result.decision,
                "summary": review_result.summary,
                "issues": review_result.issues,
                "next_action": review_result.next_action,
            },
        )

    # =========================
    # DISPLAY REVIEW RESULT
    # =========================

    print(
        "\n================================"
    )
    print(
        "REVIEW RESULT"
    )
    print(
        "================================"
    )

    print(
        "Decision:",
        review_result.decision
    )

    print(
        "Summary:",
        review_result.summary
    )

    print(
        "Issues:",
        review_result.issues
    )

    print(
        "Next Action:",
        review_result.next_action
    )

    print(
        "Next Phase:",
        review_result.next_phase
    )

    print(
        "================================"
    )

    return PhaseExecutionResult(
        review_result=review_result,
        implementer_interaction_id=implementer_interaction_id,
        implementer_result=implementer_result,
        report_content=report_content,
    )
