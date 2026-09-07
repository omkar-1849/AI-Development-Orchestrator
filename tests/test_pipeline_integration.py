import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.orchestrator.events import EventType, OrchestratorEvent
from src.orchestrator.pipeline import run_orchestrator
from src.planner.planner_contract import PlannerTask
from src.reviewer.review_contract import ReviewResult


class TestPipelineEventIntegration(unittest.TestCase):

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
    def test_run_orchestrator_emits_events_and_saves_report(
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

        review_stop = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All acceptance criteria satisfied",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        mock_phase_result = MagicMock(
            review_result=review_stop,
            implementer_interaction_id=1,
            implementer_result=MagicMock(success=True),
            report_content="# Phase 1 Report",
        )
        mock_run_phase.return_value = mock_phase_result

        emitted_events = []

        def event_listener(event: OrchestratorEvent):
            emitted_events.append(event)

        run_orchestrator(
            project_name="TestApp",
            project_path=self.temp_dir,
            user_requirements="Build a full demo application.",
            event_callback=event_listener,
        )

        event_types = [e.event_type for e in emitted_events]

        # Verify key pipeline events occurred in order
        self.assertIn(EventType.PROJECT_SETUP_STARTED, event_types)
        self.assertIn(EventType.EXPLORER_WORKSPACE_OPENED, event_types)
        self.assertIn(EventType.REQUIREMENTS_RECEIVED, event_types)
        self.assertIn(EventType.PLANNER_STARTED, event_types)
        self.assertIn(EventType.PLANNER_RESPONSE_RECEIVED, event_types)
        self.assertIn(EventType.PLANNER_VALIDATED, event_types)
        self.assertIn(EventType.WORKER_STARTED, event_types)
        self.assertIn(EventType.TASK_DISPATCHED, event_types)
        self.assertIn(EventType.PROJECT_COMPLETED, event_types)

        # Verify final project report was created on disk
        report_path = os.path.join(self.temp_dir, "final_project_report.md")
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Final Project Report: TestApp", content)
        self.assertIn("Build a full demo application.", content)
        self.assertIn("PROJECT STATUS: SUCCESSFULLY COMPLETED", content)


if __name__ == "__main__":
    unittest.main()
