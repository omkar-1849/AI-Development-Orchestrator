import os
import unittest
from unittest.mock import MagicMock, patch

import win32con

from src.automation.application_discovery import (
    ANTIGRAVITY_TARGET,
    CLAUDE_TARGET,
    ApplicationActivationError,
    ApplicationDiscovery,
    ApplicationDiscoveryError,
    ApplicationFocusError,
    ApplicationLaunchError,
    ApplicationNotFoundError,
    ApplicationStartupTimeoutError,
    ApplicationTarget,
)


class TestApplicationDiscovery(unittest.TestCase):

    def setUp(self):
        self.discovery = ApplicationDiscovery(
            discovery_timeout=0.1,
            startup_timeout=0.2,
            activation_retries=2,
        )

    # 1. Visible window discovered
    @patch("win32gui.EnumWindows")
    @patch("win32gui.IsWindowVisible")
    @patch("win32gui.GetWindowText")
    @patch("win32gui.GetClassName")
    @patch("win32process.GetWindowThreadProcessId")
    @patch("psutil.Process")
    def test_visible_window_discovered(
        self,
        mock_process,
        mock_get_pid,
        mock_get_class,
        mock_get_text,
        mock_is_visible,
        mock_enum,
    ):
        mock_is_visible.return_value = True
        mock_get_text.return_value = "Claude Desktop"
        mock_get_class.return_value = "Chrome_WidgetWin_1"
        mock_get_pid.return_value = (100, 4321)
        proc_inst = MagicMock()
        proc_inst.name.return_value = "claude.exe"
        mock_process.return_value = proc_inst

        def fake_enum(cb, extra):
            cb(1234, extra)
            return True

        mock_enum.side_effect = fake_enum

        found = self.discovery.find_visible_window(CLAUDE_TARGET)
        self.assertIsNotNone(found)
        self.assertEqual(found, (1234, "Claude Desktop", "claude.exe"))

    # 2. Existing application not launched again
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "launch_application")
    @patch.object(ApplicationDiscovery, "restore_window")
    @patch.object(ApplicationDiscovery, "activate_window")
    @patch.object(ApplicationDiscovery, "verify_foreground")
    def test_existing_application_not_launched_again(
        self,
        mock_verify,
        mock_activate,
        mock_restore,
        mock_launch,
        mock_find,
    ):
        mock_find.return_value = (1234, "Claude Desktop", "claude.exe")
        mock_restore.return_value = True
        mock_activate.return_value = True
        mock_verify.return_value = True

        result = self.discovery.ensure_application_ready(CLAUDE_TARGET)

        mock_launch.assert_not_called()
        self.assertEqual(result, (1234, "Claude Desktop", "claude.exe"))

    # 3. Minimized window restored
    @patch("win32gui.IsIconic")
    @patch("win32gui.ShowWindow")
    @patch("time.sleep")
    def test_minimized_window_restored(self, mock_sleep, mock_show, mock_is_iconic):
        mock_is_iconic.return_value = True

        restored = self.discovery.restore_window(1234)

        self.assertTrue(restored)
        mock_is_iconic.assert_called_once_with(1234)
        mock_show.assert_called_once_with(1234, win32con.SW_RESTORE)

    # 4. Window activated
    @patch.object(ApplicationDiscovery, "restore_window")
    @patch.object(ApplicationDiscovery, "verify_foreground")
    @patch("win32process.GetWindowThreadProcessId")
    @patch("win32gui.SetForegroundWindow")
    @patch("time.sleep")
    def test_window_activated(
        self,
        mock_sleep,
        mock_set_fg,
        mock_get_pid,
        mock_verify,
        mock_restore,
    ):
        mock_restore.return_value = True
        # First check returns False, second check (after strategy) returns True
        mock_verify.side_effect = [False, True]
        mock_get_pid.return_value = (100, 4321)

        result = self.discovery.activate_window(1234)

        self.assertTrue(result)
        mock_restore.assert_called_once_with(1234)

    # 5. Foreground verification succeeds
    @patch("win32gui.GetForegroundWindow")
    def test_foreground_verification(self, mock_get_fg):
        mock_get_fg.return_value = 1234
        self.assertTrue(self.discovery.verify_foreground(1234))

        mock_get_fg.return_value = 9999
        self.assertFalse(self.discovery.verify_foreground(1234))

    # 6. Launch occurs when application is absent
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "launch_application")
    @patch.object(ApplicationDiscovery, "wait_for_window")
    @patch.object(ApplicationDiscovery, "restore_window")
    @patch.object(ApplicationDiscovery, "activate_window")
    @patch.object(ApplicationDiscovery, "verify_foreground")
    def test_launch_occurs_when_application_absent(
        self,
        mock_verify,
        mock_activate,
        mock_restore,
        mock_wait,
        mock_launch,
        mock_find,
    ):
        # Initial search finds nothing
        mock_find.return_value = None
        mock_launch.return_value = True
        mock_wait.return_value = (5678, "Claude Desktop", "claude.exe")
        mock_restore.return_value = True
        mock_activate.return_value = True
        mock_verify.return_value = True

        result = self.discovery.ensure_application_ready(CLAUDE_TARGET)

        mock_launch.assert_called_once_with(CLAUDE_TARGET)
        mock_wait.assert_called_once()
        self.assertEqual(result, (5678, "Claude Desktop", "claude.exe"))

    # 7. Waits for window after launch
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch("time.sleep")
    def test_waits_for_window_after_launch(self, mock_sleep, mock_find):
        # Simulate window appearing on the second poll
        mock_find.side_effect = [None, (5678, "Claude Desktop", "claude.exe")]

        result = self.discovery.wait_for_window(CLAUDE_TARGET, timeout=1.0)

        self.assertEqual(result, (5678, "Claude Desktop", "claude.exe"))
        self.assertEqual(mock_find.call_count, 2)

    # 8. Startup timeout fails safely (ApplicationStartupTimeoutError)
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "find_process")
    @patch("time.sleep")
    def test_startup_timeout_fails_safely(self, mock_sleep, mock_proc, mock_find):
        mock_find.return_value = None
        mock_proc.return_value = None

        with self.assertRaises(ApplicationStartupTimeoutError) as ctx:
            self.discovery.wait_for_window(CLAUDE_TARGET, timeout=0.05)

        self.assertIn("Timed out", str(ctx.exception))
        self.assertIn("Claude", str(ctx.exception))

    # 9. Activation failure handled safely (ApplicationActivationError)
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "restore_window")
    @patch.object(ApplicationDiscovery, "activate_window")
    def test_activation_failure_handled_safely(
        self,
        mock_activate,
        mock_restore,
        mock_find,
    ):
        mock_find.return_value = (1234, "Claude Desktop", "claude.exe")
        mock_restore.return_value = True
        mock_activate.return_value = False

        with self.assertRaises(ApplicationActivationError) as ctx:
            self.discovery.ensure_application_ready(CLAUDE_TARGET)

        self.assertIn("Failed to activate window", str(ctx.exception))
        self.assertIn("1234", str(ctx.exception))

    # 10. Focus verification failure handled (ApplicationFocusError)
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "restore_window")
    @patch.object(ApplicationDiscovery, "activate_window")
    @patch.object(ApplicationDiscovery, "verify_foreground")
    def test_focus_verification_failure_handled(
        self,
        mock_verify,
        mock_activate,
        mock_restore,
        mock_find,
    ):
        mock_find.return_value = (1234, "Claude Desktop", "claude.exe")
        mock_restore.return_value = True
        mock_activate.return_value = True
        mock_verify.return_value = False  # Focus check fails after activation

        with self.assertRaises(ApplicationFocusError) as ctx:
            self.discovery.ensure_application_ready(CLAUDE_TARGET)

        self.assertIn("did not achieve foreground focus", str(ctx.exception))

    # 11. Claude target configuration works
    def test_claude_target_configuration(self):
        self.assertEqual(CLAUDE_TARGET.name, "Claude")
        self.assertIn("claude", CLAUDE_TARGET.window_title_patterns)
        self.assertIn("claude.exe", CLAUDE_TARGET.process_patterns)
        self.assertIn("Chrome_WidgetWin_1", CLAUDE_TARGET.window_classes)
        self.assertEqual(CLAUDE_TARGET.env_path_var, "CLAUDE_APP_PATH")
        self.assertIn("Claude.exe", CLAUDE_TARGET.default_exe_names)

        with patch.object(self.discovery, "enumerate_visible_windows") as mock_enum:
            mock_enum.return_value = [
                (101, "Document - Word", "winword.exe", "OpusApp"),
                (102, "Claude Desktop", "claude.exe", "Chrome_WidgetWin_1"),
            ]
            res = self.discovery.find_visible_window(CLAUDE_TARGET)
            self.assertEqual(res, (102, "Claude Desktop", "claude.exe"))

    # 12. Antigravity target configuration works
    def test_antigravity_target_configuration(self):
        self.assertEqual(ANTIGRAVITY_TARGET.name, "Antigravity")
        self.assertIn("antigravity", ANTIGRAVITY_TARGET.window_title_patterns)
        self.assertIn("antigravity.exe", ANTIGRAVITY_TARGET.process_patterns)
        self.assertIn("Chrome_WidgetWin_1", ANTIGRAVITY_TARGET.window_classes)
        self.assertEqual(ANTIGRAVITY_TARGET.env_path_var, "ANTIGRAVITY_APP_PATH")
        self.assertIn("Antigravity.exe", ANTIGRAVITY_TARGET.default_exe_names)

        with patch.object(self.discovery, "enumerate_visible_windows") as mock_enum:
            mock_enum.return_value = [
                (201, "Antigravity IDE", "antigravity.exe", "Chrome_WidgetWin_1"),
            ]
            res = self.discovery.find_visible_window(ANTIGRAVITY_TARGET)
            self.assertEqual(res, (201, "Antigravity IDE", "antigravity.exe"))

    # 13. Bounded retries respected
    @patch.object(ApplicationDiscovery, "restore_window")
    @patch.object(ApplicationDiscovery, "verify_foreground")
    @patch("win32process.GetWindowThreadProcessId")
    @patch("win32gui.SetForegroundWindow")
    @patch("time.sleep")
    def test_bounded_retries_respected(
        self,
        mock_sleep,
        mock_set_fg,
        mock_get_pid,
        mock_verify,
        mock_restore,
    ):
        mock_restore.return_value = True
        mock_verify.return_value = False  # Never succeeds
        mock_get_pid.return_value = (100, 4321)

        result = self.discovery.activate_window(1234, retries=2)

        self.assertFalse(result)
        # Should verify foreground initial check + (2 retries * 5 strategies) = 11 checks
        self.assertEqual(mock_verify.call_count, 11)

    # 14. Diagnostics contain meaningful failure information
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "find_process")
    @patch("time.sleep")
    def test_diagnostics_contain_meaningful_failure_info(
        self,
        mock_sleep,
        mock_find_proc,
        mock_find_win,
    ):
        mock_find_win.return_value = None
        mock_proc = MagicMock()
        mock_proc.pid = 9988
        mock_find_proc.return_value = mock_proc

        with self.assertRaises(ApplicationStartupTimeoutError) as ctx:
            self.discovery.wait_for_window(CLAUDE_TARGET, timeout=0.01)

        err_msg = str(ctx.exception)
        self.assertIn("Claude", err_msg)
        self.assertIn("Diagnostics:", err_msg)
        self.assertIn("Process running (PID 9988)", err_msg)
        self.assertIn("No visible matching window detected", err_msg)

    # 15. Launch failure when executable not found
    @patch.object(ApplicationDiscovery, "find_visible_window")
    @patch.object(ApplicationDiscovery, "launch_application")
    def test_launch_failure_raises_application_launch_error(
        self,
        mock_launch,
        mock_find,
    ):
        mock_find.return_value = None
        mock_launch.return_value = False

        with self.assertRaises(ApplicationLaunchError) as ctx:
            self.discovery.ensure_application_ready(CLAUDE_TARGET)

        self.assertIn("Could not launch 'Claude'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
