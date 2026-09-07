import unittest
from unittest.mock import patch, MagicMock

from src.orchestrator.setup import (
    OrchestratorSetup,
    setup_orchestrator,
)
from src.orchestrator.phase_runner import (
    PhaseExecutionResult,
)
from src.orchestrator.pipeline import (
    run_orchestrator,
)
from src.reviewer.review_contract import ReviewResult
from src.state.workflow_state import WorkflowState


class TestOrchestratorModules(unittest.TestCase):

    def test_setup_orchestrator_initialization(self):
        sample_request = "Build a REST API with FastAPI"
        setup = setup_orchestrator(
            project_name="CustomProject",
            project_path="C:/custom/path",
            requirement_collector=lambda: sample_request,
        )

        self.assertIsInstance(setup, OrchestratorSetup)
        self.assertEqual(setup.project_name, "CustomProject")
        self.assertEqual(setup.project_path, "C:/custom/path")
        self.assertEqual(setup.user_request, sample_request)
        self.assertEqual(setup.phase_state.current_phase, 1)
        self.assertEqual(setup.phase_state.current_attempt, 1)
        self.assertEqual(setup.workflow.current_state, WorkflowState.IDLE)

    def test_phase_execution_result_structure(self):
        review = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="Implementation looks good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )
        result = PhaseExecutionResult(
            review_result=review,
            implementer_interaction_id=42,
            implementer_result={"output": "Done"},
            report_content="# Phase 1 Report\nSuccess",
        )

        self.assertEqual(result.review_result.decision, "APPROVED")
        self.assertEqual(result.review_result.next_action, "STOP")
        self.assertEqual(result.implementer_interaction_id, 42)
        self.assertEqual(result.report_content, "# Phase 1 Report\nSuccess")

    @patch("src.orchestrator.pipeline.find_claude", return_value=None)
    @patch("builtins.print")
    def test_run_orchestrator_handles_missing_claude_gracefully(self, mock_print, mock_find):
        # When Claude window is not found, run_orchestrator should transition
        # workflow to ERROR and print error message without crashing unhandled.
        setup = setup_orchestrator(
            project_name="TestProject",
            project_path="C:/test/path",
            requirement_collector=lambda: "Test requirement",
        )
        with patch("src.orchestrator.pipeline.setup_orchestrator", return_value=setup):
            run_orchestrator(
                project_name="TestProject",
                project_path="C:/test/path",
            )
            self.assertEqual(setup.workflow.current_state, WorkflowState.ERROR)

    def test_main_imports_run_orchestrator(self):
        import main
        self.assertTrue(hasattr(main, "run_orchestrator"))
        self.assertTrue(hasattr(main, "main"))


if __name__ == "__main__":
    unittest.main()
