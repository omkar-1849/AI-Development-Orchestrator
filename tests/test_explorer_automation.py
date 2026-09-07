import hashlib
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.automation.explorer_automation import (
    ExplorerAutomation,
    ExplorerConfig,
    ExplorerAutomationError,
    WorkspaceNotFoundError,
    ReportFileNotFoundError,
    ExplorerWindowNotFoundError,
    open_project_workspace,
    select_report_file,
)
from src.state.phase_state import PhaseState


class TestExplorerAutomation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_dir = Path(self.temp_dir) / "CustomUserProject"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = self.workspace_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Config with 0 display duration and short timeouts for test speed
        self.fast_config = ExplorerConfig(
            workspace_display_duration=0.0,
            report_display_duration=0.0,
            window_find_timeout=0.5,
            poll_interval=0.05,
            strict_mode=True,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ------------------------------------------------------------
    # Test 1: Dynamic project path acceptance
    # ------------------------------------------------------------
    def test_dynamic_project_path_acceptance(self):
        """Verify that arbitrary dynamic project paths are accepted without hardcoding."""
        arbitrary_path = self.workspace_dir / "subdir" / "another_level"
        arbitrary_path.mkdir(parents=True, exist_ok=True)

        automation = ExplorerAutomation(config=self.fast_config)
        with patch("subprocess.Popen") as mock_popen, \
             patch.object(automation, "_find_new_window", return_value=12345), \
             patch.object(automation, "_activate_window", return_value=True), \
             patch.object(automation, "close_controlled_window", return_value=True):

            success = automation.open_workspace(arbitrary_path)
            self.assertTrue(success)

            # Check that Popen was called with the exact dynamic resolved path
            mock_popen.assert_called_once()
            args, _ = mock_popen.call_args
            self.assertEqual(args[0], ["explorer.exe", str(arbitrary_path.resolve())])

    # ------------------------------------------------------------
    # Test 2: Correct reports directory resolution
    # ------------------------------------------------------------
    def test_reports_directory_resolution(self):
        """Verify that reports directory is resolved relative to project path."""
        report_file = self.reports_dir / "phase_1_attempt_1.md"
        report_file.write_text("# Report 1")

        automation = ExplorerAutomation(config=self.fast_config)
        with patch("subprocess.Popen") as mock_popen, \
             patch.object(automation, "_find_new_window", return_value=12345), \
             patch.object(automation, "_activate_window", return_value=True), \
             patch.object(automation, "close_controlled_window", return_value=True):

            # Pass relative report path
            success = automation.select_report_file(
                self.workspace_dir, "reports/phase_1_attempt_1.md"
            )
            self.assertTrue(success)

            args, _ = mock_popen.call_args
            expected_flag = f"/select,{str(report_file.resolve())}"
            self.assertEqual(args[0], ["explorer.exe", expected_flag])

    # ------------------------------------------------------------
    # Test 3: Correct expected report filename resolution
    # ------------------------------------------------------------
    def test_expected_report_filename_resolution(self):
        """Verify that report filenames are properly resolved and passed."""
        report_file = self.reports_dir / "phase_2_attempt_3.md"
        report_file.write_text("# Phase 2 Attempt 3")

        automation = ExplorerAutomation(config=self.fast_config)
        with patch("subprocess.Popen") as mock_popen, \
             patch.object(automation, "_find_new_window", return_value=99999), \
             patch.object(automation, "_activate_window", return_value=True), \
             patch.object(automation, "close_controlled_window", return_value=True):

            automation.select_report_file(
                self.workspace_dir, "reports/phase_2_attempt_3.md"
            )
            args, _ = mock_popen.call_args
            self.assertIn("phase_2_attempt_3.md", args[0][1])

    # ------------------------------------------------------------
    # Test 4: Validation when workspace does not exist
    # ------------------------------------------------------------
    def test_validation_when_workspace_does_not_exist(self):
        """Verify that WorkspaceNotFoundError is raised when workspace does not exist."""
        non_existent = Path(self.temp_dir) / "NonExistentWorkspace"
        automation = ExplorerAutomation(config=self.fast_config)

        with self.assertRaises(WorkspaceNotFoundError):
            automation.open_workspace(non_existent)

    # ------------------------------------------------------------
    # Test 5: Validation when report file does not exist
    # ------------------------------------------------------------
    def test_validation_when_report_file_does_not_exist(self):
        """Verify that ReportFileNotFoundError is raised when report file does not exist."""
        automation = ExplorerAutomation(config=self.fast_config)

        with self.assertRaises(ReportFileNotFoundError):
            automation.select_report_file(
                self.workspace_dir, "reports/non_existent_report.md"
            )

    # ------------------------------------------------------------
    # Test 6: Window ownership tracking logic where mockable
    # ------------------------------------------------------------
    def test_window_ownership_tracking_diff(self):
        """Verify that newly opened HWND is detected via set diff from baseline."""
        automation = ExplorerAutomation(config=self.fast_config)

        baseline_hwnds = {101, 102, 103}
        # First poll: still baseline; Second poll: new HWND 205 appears
        poll_results = [
            {101, 102, 103},
            {101, 102, 103, 205},
        ]

        with patch("src.automation.explorer_automation.get_cabinet_hwnds", side_effect=poll_results):
            found_hwnd = automation._find_new_window(baseline_hwnds, timeout=1.0)
            self.assertEqual(found_hwnd, 205)

    # ------------------------------------------------------------
    # Test 7: Ensure close operation targets only the controlled window
    # ------------------------------------------------------------
    def test_close_targets_only_controlled_window(self):
        """Verify that close_controlled_window only targets the controlled HWND and protects baseline."""
        automation = ExplorerAutomation(config=self.fast_config)
        baseline_hwnds = {101, 102, 103}
        automation._before_hwnds = baseline_hwnds
        automation._controlled_hwnd = 205

        with patch("win32gui.IsWindow", return_value=True), \
             patch("win32gui.PostMessage") as mock_post, \
             patch("src.automation.explorer_automation.get_cabinet_hwnds", return_value=baseline_hwnds):

            closed = automation.close_controlled_window(timeout=0.2)
            self.assertTrue(closed)
            # WM_CLOSE must be posted to 205 only
            mock_post.assert_called_once_with(205, 16, 0, 0)  # 16 is win32con.WM_CLOSE
            self.assertIsNone(automation.controlled_hwnd)

    def test_close_protects_baseline_window_if_in_before_set(self):
        """Verify that if controlled_hwnd is accidentally in _before_hwnds, it is NEVER closed."""
        automation = ExplorerAutomation(config=self.fast_config)
        baseline_hwnds = {101, 102}
        automation._before_hwnds = baseline_hwnds
        automation._controlled_hwnd = 101  # Pretend it somehow matched a user window

        with patch("win32gui.PostMessage") as mock_post:
            automation.close_controlled_window()
            mock_post.assert_not_called()
            self.assertIsNone(automation.controlled_hwnd)

    # ------------------------------------------------------------
    # Test 8: Ensure no file modification methods are used
    # ------------------------------------------------------------
    def test_no_file_modification_on_select(self):
        """Verify that select_report_file does NOT modify file content, hash, or mtime."""
        report_file = self.reports_dir / "phase_1_attempt_1.md"
        original_content = "# Sensitive Report Content\nNo edits allowed!"
        report_file.write_text(original_content, encoding="utf-8")

        initial_stat = report_file.stat()
        initial_hash = hashlib.sha256(report_file.read_bytes()).hexdigest()

        automation = ExplorerAutomation(config=self.fast_config)
        with patch("subprocess.Popen"), \
             patch.object(automation, "_find_new_window", return_value=555), \
             patch.object(automation, "_activate_window", return_value=True), \
             patch.object(automation, "close_controlled_window", return_value=True):

            automation.select_report_file(
                self.workspace_dir, "reports/phase_1_attempt_1.md"
            )

        post_stat = report_file.stat()
        post_hash = hashlib.sha256(report_file.read_bytes()).hexdigest()

        self.assertEqual(initial_hash, post_hash)
        self.assertEqual(original_content, report_file.read_text(encoding="utf-8"))
        self.assertEqual(initial_stat.st_mtime, post_stat.st_mtime)

    # ------------------------------------------------------------
    # Test 9: Ensure phase/attempt report paths are dynamic
    # ------------------------------------------------------------
    def test_phase_state_dynamic_report_resolution(self):
        """Verify that PhaseState dynamic report path generation works across phases and retries."""
        ps = PhaseState(project_name="TestProject")
        self.assertEqual(ps.get_report_filename(), "phase_1_attempt_1.md")
        self.assertEqual(ps.get_report_path(), "reports/phase_1_attempt_1.md")

        # Retry attempt
        ps.next_attempt()
        self.assertEqual(ps.get_report_filename(), "phase_1_attempt_2.md")
        self.assertEqual(ps.get_report_path(), "reports/phase_1_attempt_2.md")

        # Next phase
        ps.next_phase()
        self.assertEqual(ps.get_report_filename(), "phase_2_attempt_1.md")
        self.assertEqual(ps.get_report_path(), "reports/phase_2_attempt_1.md")

        # Retry phase 2
        ps.next_attempt()
        self.assertEqual(ps.get_report_filename(), "phase_2_attempt_2.md")
        self.assertEqual(ps.get_report_path(), "reports/phase_2_attempt_2.md")

        # Verify automation correctly accepts these dynamic paths
        automation = ExplorerAutomation(config=self.fast_config)
        report_file_p2a2 = self.reports_dir / ps.get_report_filename()
        report_file_p2a2.write_text("# Phase 2 Attempt 2 Report")

        with patch("subprocess.Popen") as mock_popen, \
             patch.object(automation, "_find_new_window", return_value=777), \
             patch.object(automation, "_activate_window", return_value=True), \
             patch.object(automation, "close_controlled_window", return_value=True):

            success = automation.select_report_file(
                self.workspace_dir, ps.get_report_path()
            )
            self.assertTrue(success)
            args, _ = mock_popen.call_args
            self.assertIn("phase_2_attempt_2.md", args[0][1])

    # ------------------------------------------------------------
    # Test 10: Helper functions invocation
    # ------------------------------------------------------------
    def test_convenience_functions(self):
        """Verify open_project_workspace and select_report_file helper functions."""
        report_file = self.reports_dir / "phase_1_attempt_1.md"
        report_file.write_text("# Report")

        with patch("src.automation.explorer_automation.ExplorerAutomation.open_workspace", return_value=True) as mock_open:
            result = open_project_workspace(self.workspace_dir)
            self.assertTrue(result)
            mock_open.assert_called_once_with(
                project_path=self.workspace_dir,
                display_duration=None,
            )

        with patch("src.automation.explorer_automation.ExplorerAutomation.select_report_file", return_value=True) as mock_select:
            result = select_report_file(self.workspace_dir, "reports/phase_1_attempt_1.md")
            self.assertTrue(result)
            mock_select.assert_called_once_with(
                project_path=self.workspace_dir,
                report_path="reports/phase_1_attempt_1.md",
                display_duration=None,
            )

    # ------------------------------------------------------------
    # Test 11: Lifecycle Integration in phase_runner
    # ------------------------------------------------------------
    def test_phase_runner_invokes_explorer_report_selection(self):
        """Verify that phase_runner calls select_report_file after report reception."""
        from src.orchestrator.phase_runner import run_phase
        from src.orchestrator.events import EventType
        from src.reviewer.review_contract import ReviewResult

        report_file = self.reports_dir / "phase_1_attempt_1.md"
        report_file.write_text("# Phase 1 Report\n<!-- REPORT_END -->")

        worker_task = MagicMock(task_id="TASK-001", objective="Test Objective")
        phase_state = PhaseState(project_name="CustomUserProject")
        workflow = MagicMock()
        manager = MagicMock()
        manager.execute_task.return_value = MagicMock(success=True, output="Done")
        claude = MagicMock()

        events = []
        def listener(evt):
            events.append(evt)

        review = ReviewResult(
            review_id="REV-001",
            decision="APPROVED",
            phase_completed=1,
            summary="All good",
            issues=[],
            next_action="STOP",
            next_phase=None,
        )

        with patch("src.orchestrator.phase_runner.wait_for_report", return_value="# Phase 1 Report\n<!-- REPORT_END -->"), \
             patch("src.orchestrator.phase_runner.build_review_prompt", return_value="Review prompt"), \
             patch("src.orchestrator.phase_runner.send_prompt"), \
             patch("src.orchestrator.phase_runner.wait_for_response"), \
             patch("src.orchestrator.phase_runner.capture_latest_response", return_value="{}"), \
             patch("src.orchestrator.phase_runner.validate_review_response", return_value=review), \
             patch("src.orchestrator.phase_runner.save_interaction", return_value=1), \
             patch("src.orchestrator.phase_runner.select_report_file") as mock_select_report:

            result = run_phase(
                worker_task=worker_task,
                phase_state=phase_state,
                workflow=workflow,
                manager=manager,
                claude=claude,
                project_name="CustomUserProject",
                project_path=str(self.workspace_dir),
                event_callback=listener,
            )

            mock_select_report.assert_called_once_with(
                project_path=str(self.workspace_dir),
                report_path="reports/phase_1_attempt_1.md",
            )
            event_types = [e.event_type for e in events]
            self.assertIn(EventType.EXPLORER_REPORT_SELECTED, event_types)


if __name__ == "__main__":
    unittest.main()
