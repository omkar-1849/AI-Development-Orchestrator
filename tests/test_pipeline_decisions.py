import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.orchestrator.events import EventType, OrchestratorEvent
from src.orchestrator.pipeline import run_orchestrator
from src.planner.planner_contract import PlannerTask
from src.reviewer.review_contract import ReviewResult


def _setup_mocks(
    mock_find_claude,
    mock_capture_response,
    mock_validate_planner,
    mock_dispatch_task
):
    mock_find_claude.return_value = MagicMock()
    mock_capture_response.return_value = '{"objective": "test"}'
    mock_validate_planner.return_value = PlannerTask(
        task_id="TASK-001",
        status="READY",
        objective="Build demo feature",
        instructions=["Do this"],
        files_allowed=["demo.py"],
        acceptance_criteria=["Works"],
    )
    mock_dispatch_task.return_value = MagicMock(
        task_id="TASK-001",
        objective="Build demo feature",
    )


class TestPipelineDecisions(unittest.TestCase):

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
    def test_blocked_stop_never_success(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_blocked = ReviewResult(
            review_id="REV-001",
            decision="BLOCKED",
            phase_completed=1,
            summary="Critical issue",
            issues=["Missing file"],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(
            review_result=review_blocked,
            implementer_interaction_id=1,
            implementer_result=MagicMock(success=True),
        )

        emitted_events = []
        def event_listener(event: OrchestratorEvent):
            emitted_events.append(event)

        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=event_listener,
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.PROJECT_BLOCKED, event_types)
        self.assertNotIn(EventType.PROJECT_COMPLETED, event_types)
        self.assertIn(EventType.PROJECT_FAILED, event_types)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_blocked_with_any_next_action(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_blocked = ReviewResult(
            review_id="REV-002",
            decision="BLOCKED",
            phase_completed=1,
            summary="System error",
            issues=[],
            next_action="NEXT_PHASE",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_blocked)

        emitted_events = []
        
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.PROJECT_BLOCKED, event_types)
        self.assertNotIn(EventType.NEXT_PHASE, event_types)
        self.assertIn(EventType.PROJECT_FAILED, event_types)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_approved_stop_is_success(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_success = ReviewResult(
            review_id="REV-003",
            decision="APPROVED",
            phase_completed=1,
            summary="All good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_run_phase.return_value = MagicMock(review_result=review_success)

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.PROJECT_COMPLETED, event_types)
        self.assertNotIn(EventType.PROJECT_FAILED, event_types)

    @patch("src.orchestrator.pipeline.dispatch_next_phase")
    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_approved_next_phase_progresses(
        self,
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_next = ReviewResult(
            review_id="REV-004",
            decision="APPROVED",
            phase_completed=1,
            summary="Phase 1 good",
            issues=[],
            next_action="NEXT_PHASE",
            next_phase={"objective": "Phase 2"},
        )
        
        review_stop = ReviewResult(
            review_id="REV-005",
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
        
        mock_dispatch_next_phase.return_value = MagicMock(task_id="TASK-002")

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.NEXT_PHASE, event_types)
        self.assertIn(EventType.PROJECT_COMPLETED, event_types)
        self.assertEqual(mock_run_phase.call_count, 2)
        mock_dispatch_next_phase.assert_called_once()

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_correction_needed_retry_phase(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_retry = ReviewResult(
            review_id="REV-006",
            decision="CORRECTION_NEEDED",
            phase_completed=1,
            summary="Needs fix",
            issues=["Typo in code"],
            next_action="RETRY_PHASE",
            next_phase=None,
        )
        
        review_stop = ReviewResult(
            review_id="REV-007",
            decision="APPROVED",
            phase_completed=1,
            summary="Fixed",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        
        mock_run_phase.side_effect = [
            MagicMock(review_result=review_retry),
            MagicMock(review_result=review_stop),
        ]

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.RETRY_PHASE, event_types)
        self.assertIn(EventType.PROJECT_COMPLETED, event_types)
        self.assertEqual(mock_run_phase.call_count, 2)
        
    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_replan_is_failure(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_replan = ReviewResult(
            review_id="REV-008",
            decision="REPLAN",
            phase_completed=1,
            summary="Architecture wrong",
            issues=[],
            next_action="ANY",
            next_phase=None,
        )
        
        mock_run_phase.return_value = MagicMock(review_result=review_replan)

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertIn(EventType.PROJECT_BLOCKED, event_types)
        self.assertIn(EventType.PROJECT_FAILED, event_types)
        
    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_invalid_combination_fails(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_invalid = ReviewResult(
            review_id="REV-009",
            decision="APPROVED",
            phase_completed=1,
            summary="Good",
            issues=[],
            next_action="RETRY_PHASE",
            next_phase=None,
        )
        
        mock_run_phase.return_value = MagicMock(review_result=review_invalid)

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        event_types = [e.event_type for e in emitted_events]
        self.assertNotIn(EventType.PROJECT_COMPLETED, event_types)
        self.assertIn(EventType.PROJECT_FAILED, event_types)
        
        failed_event = next(e for e in emitted_events if e.event_type == EventType.PROJECT_FAILED)
        self.assertIn("Unhandled reviewer decision", failed_event.message)

    @patch("src.orchestrator.pipeline.find_claude")
    @patch("src.orchestrator.pipeline.send_prompt")
    @patch("src.orchestrator.pipeline.wait_for_response")
    @patch("src.orchestrator.pipeline.capture_latest_response")
    @patch("src.orchestrator.pipeline.validate_planner_response")
    @patch("src.orchestrator.pipeline.dispatch_task")
    @patch("src.orchestrator.pipeline.AntigravityAutomation")
    @patch("src.orchestrator.pipeline.run_phase")
    def test_retry_stores_feedback(
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
        _setup_mocks(mock_find_claude, mock_capture_response, mock_validate_planner, mock_dispatch_task)
        
        review_retry = ReviewResult(
            review_id="REV-010",
            decision="CORRECTION_NEEDED",
            phase_completed=1,
            summary="Needs fix",
            issues=["Typo in code", "Missing test"],
            next_action="RETRY_PHASE",
            next_phase=None,
        )
        
        review_stop = ReviewResult(
            review_id="REV-011",
            decision="APPROVED",
            phase_completed=1,
            summary="Fixed",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        
        mock_run_phase.side_effect = [
            MagicMock(review_result=review_retry),
            MagicMock(review_result=review_stop),
        ]

        emitted_events = []
        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Do something",
            event_callback=lambda e: emitted_events.append(e),
        )

        retry_events = [e for e in emitted_events if e.event_type == EventType.RETRY_PHASE]
        self.assertEqual(len(retry_events), 1)
        
        self.assertEqual(retry_events[0].data["issues"], ["Typo in code", "Missing test"])


if __name__ == "__main__":
    unittest.main()
