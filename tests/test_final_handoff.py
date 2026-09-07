import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.gui.controller import OrchestratorController
from src.orchestrator.events import EventType, OrchestratorEvent
from src.orchestrator.pipeline import run_orchestrator
from src.planner.planner_contract import PlannerTask
from src.reviewer.review_contract import ReviewResult
from src.state.workflow_state import WorkflowState


def _setup_mocks(
    mock_find_claude,
    mock_capture_response,
    mock_validate_planner,
    mock_dispatch_task,
):
    mock_find_claude.return_value = MagicMock()
    mock_capture_response.return_value = '{"objective": "test"}'
    mock_validate_planner.return_value = PlannerTask(
        task_id="TASK-001",
        status="READY",
        objective="Build contact book feature",
        instructions=["Create main.py"],
        files_allowed=["main.py"],
        acceptance_criteria=["Works"],
    )
    mock_dispatch_task.return_value = MagicMock(
        task_id="TASK-001",
        objective="Build contact book feature",
        instructions=["Create main.py"],
        files_allowed=["main.py"],
        acceptance_criteria=["Works"],
    )


class TestFinalHandoff(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    @patch("src.orchestrator.pipeline.wait_for_report")
    def test_approved_stop_triggers_final_handoff(
        self,
        mock_wait_report,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """1. APPROVED + STOP triggers final handoff generation."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_success = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All acceptance criteria satisfied",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(
            review_result=review_success,
            implementer_interaction_id=1,
        )

        # Simulate Antigravity generating final_project_handoff.md
        def fake_wait_report(project_path, report_path, **kwargs):
            p = Path(project_path) / report_path
            content = "# Project Handoff: TestApp\nReady to run\n<!-- REPORT_END -->"
            p.write_text(content, encoding="utf-8")
            return content

        mock_wait_report.side_effect = fake_wait_report

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build contact book",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.HANDOFF_STARTED, event_types)
        self.assertIn(EventType.HANDOFF_PREPARING, event_types)
        self.assertIn(EventType.HANDOFF_COMPLETED, event_types)
        self.assertIn(EventType.PROJECT_COMPLETED, event_types)

        handoff_file = Path(self.temp_dir) / "final_project_handoff.md"
        self.assertTrue(handoff_file.exists())

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    @patch("src.orchestrator.pipeline.wait_for_report")
    def test_handoff_is_generated_exactly_once(
        self,
        mock_wait_report,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """2. Final handoff is generated exactly once."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_success = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_success)

        def fake_wait(project_path, report_path, **kwargs):
            p = Path(project_path) / report_path
            p.write_text("Handoff\n<!-- REPORT_END -->", encoding="utf-8")
            return "Handoff"

        mock_wait_report.side_effect = fake_wait

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build something",
            event_callback=lambda e: emitted_events.append(e),
        )

        started_count = sum(1 for e in emitted_events if e.event_type == EventType.HANDOFF_STARTED)
        completed_count = sum(1 for e in emitted_events if e.event_type == EventType.HANDOFF_COMPLETED)
        self.assertEqual(started_count, 1)
        self.assertEqual(completed_count, 1)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    @patch("src.orchestrator.pipeline.wait_for_report")
    def test_handoff_occurs_before_project_completed(
        self,
        mock_wait_report,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """3. Handoff events occur before PROJECT_COMPLETED."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_success = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_success)

        def fake_wait(project_path, report_path, **kwargs):
            p = Path(project_path) / report_path
            p.write_text("Handoff\n<!-- REPORT_END -->", encoding="utf-8")
            return "Handoff"

        mock_wait_report.side_effect = fake_wait

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        handoff_idx = event_types.index(EventType.HANDOFF_COMPLETED)
        project_completed_idx = event_types.index(EventType.PROJECT_COMPLETED)
        self.assertLess(handoff_idx, project_completed_idx)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    @patch("src.orchestrator.pipeline.wait_for_report")
    def test_handoff_failure_does_not_prevent_project_completion(
        self,
        mock_wait_report,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """4. Failure/timeout during handoff does not fail the project."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_success = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_success)
        mock_wait_report.side_effect = TimeoutError("Timed out waiting for Antigravity handoff")

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.PROJECT_COMPLETED, event_types)
        self.assertNotIn(EventType.PROJECT_FAILED, event_types)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    @patch("src.orchestrator.pipeline.wait_for_report")
    def test_fallback_handoff_is_created_when_antigravity_fails(
        self,
        mock_wait_report,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """5. Fallback final_project_handoff.md is generated when Antigravity fails."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_success = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_success)
        mock_wait_report.side_effect = RuntimeError("Antigravity crashed")

        run_orchestrator(
            project_name="FallbackApp",
            project_path=self.temp_dir,
            user_requirements="Build a simple app",
        )

        handoff_file = Path(self.temp_dir) / "final_project_handoff.md"
        self.assertTrue(handoff_file.exists())
        content = handoff_file.read_text(encoding="utf-8")
        self.assertIn("# Project Handoff: FallbackApp", content)
        self.assertIn("How to Run", content)
        self.assertIn("READY TO RUN", content)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_blocked_workflow_never_triggers_handoff(
        self,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """6. Blocked workflow never triggers handoff."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_blocked = ReviewResult(
            review_id="REV-001",
            decision="BLOCKED",
            phase_completed=1,
            summary="Blocked by missing API key",
            issues=["Missing key"],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_blocked)

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.PROJECT_BLOCKED, event_types)
        self.assertNotIn(EventType.HANDOFF_STARTED, event_types)
        self.assertNotIn(EventType.HANDOFF_COMPLETED, event_types)
        self.assertNotIn(EventType.PROJECT_COMPLETED, event_types)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_correction_needed_retry_never_triggers_handoff(
        self,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
    ):
        """7. Correction needed/retry never triggers handoff."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_retry = ReviewResult(
            review_id="REV-001",
            decision="CORRECTION_NEEDED",
            phase_completed=1,
            summary="Need fix",
            issues=["Bug"],
            next_action="RETRY_PHASE",
            next_phase=None,
        )
        # Mock max retries exceeded to terminate cleanly
        mock_run_phase.return_value = MagicMock(review_result=review_retry)

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.RETRY_PHASE, event_types)
        self.assertNotIn(EventType.HANDOFF_STARTED, event_types)
        self.assertNotIn(EventType.HANDOFF_COMPLETED, event_types)
        self.assertNotIn(EventType.PROJECT_COMPLETED, event_types)

    @patch("src.orchestrator.pipeline.dispatch_next_phase")
    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    @patch("src.orchestrator.pipeline.wait_for_report")
    def test_approved_next_phase_never_triggers_handoff(
        self,
        mock_wait_report,
        mock_run_phase,
        mock_automation,
        mock_dispatch_task,
        mock_validate_planner,
        mock_capture_response,
        mock_wait_response,
        mock_send_prompt,
        mock_find_claude,
        mock_dispatch_next_phase,
    ):
        """8. APPROVED + NEXT_PHASE never triggers handoff for that phase."""
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)

        review_next = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="Phase 1 good",
            issues=[],
            next_action="NEXT_PHASE",
            next_phase={"objective": "Phase 2"},
        )
        review_stop = ReviewResult(
            review_id="REV-002",
            decision="APPROVED",
            phase_completed=2,
            summary="Phase 2 good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.side_effect = [
            MagicMock(review_result=review_next),
            MagicMock(review_result=review_stop),
        ]
        mock_dispatch_next_phase.return_value = MagicMock(task_id="TASK-002", objective="Phase 2")

        def fake_wait(project_path, report_path, **kwargs):
            p = Path(project_path) / report_path
            p.write_text("Handoff\n<!-- REPORT_END -->", encoding="utf-8")
            return "Handoff"

        mock_wait_report.side_effect = fake_wait

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build multi-phase",
            event_callback=lambda e: emitted_events.append(e),
        )

        handoff_events = [e for e in emitted_events if e.event_type == EventType.HANDOFF_STARTED]
        self.assertEqual(len(handoff_events), 1)
        self.assertEqual(handoff_events[0].phase, 2)

    def test_gui_controller_can_retrieve_handoff_content(self):
        """9. GUI/controller can retrieve handoff content with fallback."""
        controller = OrchestratorController()
        controller.project_path = self.temp_dir

        # Nothing exists initially
        content = controller.get_final_report_content()
        self.assertIn("not yet available", content)

        # Create internal audit report only
        audit_file = Path(self.temp_dir) / "final_project_report.md"
        audit_file.write_text("# Internal Audit Report\nDetails here", encoding="utf-8")
        self.assertEqual(controller.get_final_report_content(), "# Internal Audit Report\nDetails here")

        # Create user handoff report -> becomes primary
        handoff_file = Path(self.temp_dir) / "final_project_handoff.md"
        handoff_file.write_text("# Project Handoff\nHow to run: python main.py", encoding="utf-8")
        self.assertIn("Project Handoff", controller.get_final_report_content())
        self.assertIn("How to run", controller.get_handoff_report_content())


if __name__ == "__main__":
    unittest.main()
