from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


class EventType(str, Enum):
    # Setup
    PROJECT_SETUP_STARTED = "PROJECT_SETUP_STARTED"
    PROJECT_WORKSPACE_CREATED = "PROJECT_WORKSPACE_CREATED"
    EXPLORER_WORKSPACE_OPENED = "EXPLORER_WORKSPACE_OPENED"
    REQUIREMENTS_RECEIVED = "REQUIREMENTS_RECEIVED"

    # Planner
    PLANNER_STARTED = "PLANNER_STARTED"
    PLANNER_RESPONSE_RECEIVED = "PLANNER_RESPONSE_RECEIVED"
    PLANNER_VALIDATED = "PLANNER_VALIDATED"

    # Worker
    WORKER_STARTED = "WORKER_STARTED"
    TASK_DISPATCHED = "TASK_DISPATCHED"

    # Implementation
    IMPLEMENTATION_STARTED = "IMPLEMENTATION_STARTED"
    IMPLEMENTATION_COMPLETED = "IMPLEMENTATION_COMPLETED"

    # Report
    REPORT_WAITING = "REPORT_WAITING"
    REPORT_RECEIVED = "REPORT_RECEIVED"
    EXPLORER_REPORT_SELECTED = "EXPLORER_REPORT_SELECTED"

    # Review
    REVIEW_STARTED = "REVIEW_STARTED"
    REVIEW_RESPONSE_RECEIVED = "REVIEW_RESPONSE_RECEIVED"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    REVIEW_REJECTED = "REVIEW_REJECTED"

    # Phase Transitions
    NEXT_PHASE = "NEXT_PHASE"
    RETRY_PHASE = "RETRY_PHASE"

    # Project Outcomes
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    PROJECT_BLOCKED = "PROJECT_BLOCKED"
    PROJECT_FAILED = "PROJECT_FAILED"


@dataclass
class OrchestratorEvent:
    event_type: EventType
    message: str
    phase: int = 1
    attempt: int = 1
    level: str = "INFO"  # INFO, SUCCESS, WARNING, ERROR
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%H:%M:%S")
    )
    data: Optional[Dict[str, Any]] = None


EventCallback = Callable[[OrchestratorEvent], None]


def emit_event(
    callback: Optional[EventCallback],
    event_type: EventType,
    message: str,
    phase: int = 1,
    attempt: int = 1,
    level: str = "INFO",
    data: Optional[Dict[str, Any]] = None,
) -> Optional[OrchestratorEvent]:
    """
    Safely emit an event through the provided callback if present.
    Returns the created OrchestratorEvent.
    """
    event = OrchestratorEvent(
        event_type=event_type,
        message=message,
        phase=phase,
        attempt=attempt,
        level=level,
        data=data or {},
    )
    if callback is not None:
        try:
            callback(event)
        except Exception as exc:
            print(f"[WARN] Error in event callback: {exc}")
    return event
