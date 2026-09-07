import os
import queue
import subprocess
import threading
from pathlib import Path
from typing import List, Optional, Tuple

from src.orchestrator.events import EventType, OrchestratorEvent
from src.orchestrator.pipeline import run_orchestrator
from src.project.project_manager import validate_project_name


class OrchestratorController:
    """
    Application controller separating GUI views from the Orchestrator backend.
    Manages background worker threads, thread-safe event queuing, validation,
    and filesystem interactions.
    """

    def __init__(self):
        self._event_queue: queue.Queue[OrchestratorEvent] = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None

        self.project_name: str = ""
        self.project_path: Optional[str] = None
        self.requirements: str = ""
        self.is_running: bool = False
        self.handoff_report_path: Optional[str] = None
        self.final_report_path: Optional[str] = None
        self.final_status: str = "IDLE"  # IDLE, RUNNING, COMPLETED, FAILED, BLOCKED
        self.last_error: Optional[str] = None

    def validate_inputs(self, name: str, requirements: str) -> Tuple[bool, str]:
        """
        Validate project name and requirements.
        Returns (is_valid, error_message).
        """
        if not name or not name.strip():
            return False, "Project name cannot be empty."

        try:
            validate_project_name(name)
        except ValueError as exc:
            return False, str(exc)

        if not requirements or not requirements.strip():
            return False, "Project requirements cannot be empty."

        return True, ""

    def start_orchestration(self, project_name: str, requirements: str) -> bool:
        """
        Start the orchestrator pipeline in a background worker thread.
        Returns True if started successfully, False if already running.
        """
        if self.is_running:
            return False

        valid, err = self.validate_inputs(project_name, requirements)
        if not valid:
            raise ValueError(err)

        self.project_name = project_name.strip()
        self.requirements = requirements.strip()
        self.project_path = None
        self.handoff_report_path = None
        self.final_report_path = None
        self.final_status = "RUNNING"
        self.last_error = None
        self.is_running = True

        # Clear any old queued events
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except queue.Empty:
                break

        def _worker_target():
            try:
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    h = user32.OpenInputDesktop(0, False, 0x01FF)
                    if h:
                        user32.SetThreadDesktop(h)
                except Exception:
                    pass

                run_orchestrator(
                    project_name=self.project_name,
                    project_path=None,
                    user_requirements=self.requirements,
                    event_callback=self._on_orchestrator_event,
                )
            except Exception as exc:
                self._on_orchestrator_event(
                    OrchestratorEvent(
                        event_type=EventType.PROJECT_FAILED,
                        message=f"Orchestration thread error: {exc}",
                        level="ERROR",
                        data={"error": str(exc)},
                    )
                )
            finally:
                self.is_running = False

        self._worker_thread = threading.Thread(
            target=_worker_target,
            name="OrchestratorWorkerThread",
            daemon=True,
        )
        self._worker_thread.start()
        return True

    def _on_orchestrator_event(self, event: OrchestratorEvent) -> None:
        """
        Called by background thread to push events into thread-safe queue.
        Also updates controller state variables.
        """
        # Track important paths & statuses
        if event.event_type == EventType.PROJECT_WORKSPACE_CREATED and event.data:
            self.project_path = event.data.get("project_path")
        elif event.event_type == EventType.HANDOFF_COMPLETED and event.data:
            self.handoff_report_path = event.data.get("handoff_path")
        elif event.event_type == EventType.PROJECT_COMPLETED:
            self.final_status = "COMPLETED"
            if event.data:
                self.final_report_path = event.data.get("report_path")
                if not self.handoff_report_path and event.data.get("handoff_path"):
                    self.handoff_report_path = event.data.get("handoff_path")
        elif event.event_type == EventType.PROJECT_BLOCKED:
            self.final_status = "BLOCKED"
        elif event.event_type == EventType.PROJECT_FAILED:
            self.final_status = "FAILED"
            if event.data:
                self.last_error = event.data.get("error")

        self._event_queue.put(event)

    def get_pending_events(self) -> List[OrchestratorEvent]:
        """
        Retrieve all pending events from the queue (non-blocking).
        Safe to call from GUI main thread.
        """
        events: List[OrchestratorEvent] = []
        while not self._event_queue.empty():
            try:
                events.append(self._event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def get_handoff_report_content(self) -> str:
        """Read and return user-facing final project handoff report text if available."""
        # 1. Try recorded handoff report path
        if self.handoff_report_path and os.path.exists(self.handoff_report_path):
            try:
                with open(self.handoff_report_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as exc:
                return f"Error reading handoff report: {exc}"

        # 2. Try looking in project workspace
        if self.project_path:
            candidate = Path(self.project_path) / "final_project_handoff.md"
            if candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as exc:
                    return f"Error reading handoff report: {exc}"

        return "Final project handoff report is not yet available."

    def get_final_report_content(self) -> str:
        """
        Read and return user-facing report text.
        Primary: final_project_handoff.md
        Fallback: final_project_report.md
        """
        # Primary: check if handoff report is available
        handoff = self.get_handoff_report_content()
        if handoff and not handoff.startswith("Final project handoff report is not yet available"):
            return handoff

        # Fallback 1: Try recorded report path
        if self.final_report_path and os.path.exists(self.final_report_path):
            try:
                with open(self.final_report_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as exc:
                return f"Error reading report: {exc}"

        # Fallback 2: Try looking in project workspace
        if self.project_path:
            candidate = Path(self.project_path) / "final_project_report.md"
            if candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as exc:
                    return f"Error reading report: {exc}"

        return "Final project report is not yet available."

    def open_project_folder(self) -> bool:
        """Safely open project workspace folder in Windows Explorer."""
        if not self.project_path or not os.path.exists(self.project_path):
            return False

        path_str = os.path.normpath(self.project_path)
        try:
            os.startfile(path_str)  # type: ignore[attr-defined]
            return True
        except Exception:
            try:
                subprocess.Popen(["explorer", path_str])
                return True
            except Exception:
                return False

    def reset(self) -> None:
        """Reset state for starting a new project."""
        self.project_name = ""
        self.project_path = None
        self.requirements = ""
        self.is_running = False
        self.handoff_report_path = None
        self.final_report_path = None
        self.final_status = "IDLE"
        self.last_error = None
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except queue.Empty:
                break
