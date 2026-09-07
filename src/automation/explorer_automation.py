import ctypes
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

import win32api
import win32con
import win32gui
import win32process


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class ExplorerAutomationError(Exception):
    """Base exception for all Explorer automation errors."""
    pass


class WorkspaceNotFoundError(ExplorerAutomationError, FileNotFoundError):
    """Raised when the target project workspace directory does not exist."""
    pass


class ReportFileNotFoundError(ExplorerAutomationError, FileNotFoundError):
    """Raised when the expected report file does not exist on disk."""
    pass


class ExplorerWindowNotFoundError(ExplorerAutomationError):
    """Raised when an Explorer window cannot be found after launching."""
    pass


class ExplorerNavigationTimeout(ExplorerAutomationError):
    """Raised when Explorer navigation or selection times out."""
    pass


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class ExplorerConfig:
    """
    Configuration settings for Explorer automation timings and behaviors.
    """
    workspace_display_duration: float = 2.0
    report_selection_display_duration: float = 2.0
    report_display_duration: Optional[float] = None
    window_find_timeout: float = 8.0
    navigation_timeout: float = 5.0
    poll_interval: float = 0.2
    strict_mode: bool = False
    enabled: bool = True

    def __post_init__(self):
        if self.report_display_duration is not None:
            self.report_selection_display_duration = self.report_display_duration
        else:
            self.report_display_duration = self.report_selection_display_duration


# ============================================================
# WINDOW ENUMERATION UTILITIES
# ============================================================

def get_cabinet_hwnds() -> Set[int]:
    """
    Find all visible top-level Windows File Explorer windows (class CabinetWClass).
    Returns a set of window handles (HWNDs).
    """
    hwnds: Set[int] = set()

    def _enum_callback(hwnd: int, _extra: None) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            try:
                class_name = win32gui.GetClassName(hwnd)
                if class_name == "CabinetWClass":
                    hwnds.add(hwnd)
            except Exception:
                pass
        return True

    try:
        win32gui.EnumWindows(_enum_callback, None)
    except Exception:
        pass

    return hwnds


# ============================================================
# EXPLORER AUTOMATION CONTROLLER
# ============================================================

class ExplorerAutomation:
    """
    Dedicated controller for Windows File Explorer automation.
    Tracks window ownership, ensures strictly visual context operations,
    and guarantees that only automation-opened Explorer windows are closed.
    """

    def __init__(self, config: Optional[ExplorerConfig] = None):
        self.config = config or ExplorerConfig()
        self._before_hwnds: Set[int] = set()
        self._controlled_hwnd: Optional[int] = None

    @property
    def controlled_hwnd(self) -> Optional[int]:
        """Return the window handle currently controlled by this instance."""
        return self._controlled_hwnd

    # ------------------------------------------------------------
    # Window Lifecycle & Activation
    # ------------------------------------------------------------

    def _find_new_window(self, before_hwnds: Set[int], timeout: float) -> Optional[int]:
        """
        Poll until a new CabinetWClass window handle appears that was not
        present in before_hwnds.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_hwnds = get_cabinet_hwnds()
            diff = current_hwnds - before_hwnds
            if diff:
                return next(iter(diff))
            time.sleep(self.config.poll_interval)
        return None

    def _activate_window(self, hwnd: int) -> bool:
        """
        Restore and bring the specified window to the foreground using
        a multi-strategy layered approach.
        """
        if not win32gui.IsWindow(hwnd):
            return False

        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.15)
        except Exception:
            pass

        # Strategy 1: AllowSetForegroundWindow
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            ctypes.windll.user32.AllowSetForegroundWindow(pid)
            win32gui.SetForegroundWindow(hwnd)
            if win32gui.GetForegroundWindow() == hwnd:
                return True
        except Exception:
            pass

        # Strategy 2: AttachThreadInput
        try:
            fg_hwnd = win32gui.GetForegroundWindow()
            fg_thread = win32process.GetWindowThreadProcessId(fg_hwnd)[0]
            target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]

            if fg_thread != target_thread:
                win32process.AttachThreadInput(fg_thread, target_thread, True)
                try:
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)
                finally:
                    win32process.AttachThreadInput(fg_thread, target_thread, False)
            else:
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetForegroundWindow(hwnd)

            if win32gui.GetForegroundWindow() == hwnd:
                return True
        except Exception:
            pass

        # Strategy 3: Menu (Alt) key trick
        try:
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32gui.SetForegroundWindow(hwnd)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            if win32gui.GetForegroundWindow() == hwnd:
                return True
        except Exception:
            pass

        return win32gui.GetForegroundWindow() == hwnd

    def close_controlled_window(self, timeout: float = 3.0) -> bool:
        """
        Safely close ONLY the Explorer window tracked by this automation instance.
        Verifies that the target handle is not in the baseline set.
        """
        hwnd = self._controlled_hwnd
        if not hwnd:
            return True

        if hwnd in self._before_hwnds:
            # Absolute safety guard: never close a pre-existing window
            self._controlled_hwnd = None
            return True

        if not win32gui.IsWindow(hwnd):
            self._controlled_hwnd = None
            return True

        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception as exc:
            print(f"[WARN] Error sending WM_CLOSE to Explorer window {hwnd}: {exc}")

        # Wait for the window to close
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not win32gui.IsWindow(hwnd) or hwnd not in get_cabinet_hwnds():
                self._controlled_hwnd = None
                return True
            time.sleep(0.1)

        self._controlled_hwnd = None
        return True

    # ------------------------------------------------------------
    # Cycle 1: Open Project Workspace
    # ------------------------------------------------------------

    def open_workspace(
        self,
        project_path: str | Path,
        display_duration: Optional[float] = None,
    ) -> bool:
        """
        Open Windows File Explorer navigated to the project workspace directory.
        Brings the window to foreground, holds it for the display duration,
        and closes ONLY that window.

        Args:
            project_path: Path to the dynamically created project directory.
            display_duration: Seconds to display Explorer window. If None, uses config default.

        Returns:
            bool: True if completed successfully, False if UI operation encountered non-fatal error.
        """
        if not self.config.enabled:
            return True

        # 1. Validate workspace existence
        workspace = Path(project_path)
        if not workspace.exists() or not workspace.is_dir():
            raise WorkspaceNotFoundError(
                f"Project workspace directory does not exist: {workspace}"
            )

        resolved_path = str(workspace.resolve())
        duration = (
            display_duration
            if display_duration is not None
            else self.config.workspace_display_duration
        )

        # 2. Capture existing Explorer windows before launch
        self._before_hwnds = get_cabinet_hwnds()

        # 3. Launch Explorer targeting the workspace folder
        try:
            subprocess.Popen(["explorer.exe", resolved_path])
        except Exception as exc:
            msg = f"Failed to launch Explorer for workspace {resolved_path}: {exc}"
            if self.config.strict_mode:
                raise ExplorerAutomationError(msg) from exc
            print(f"[WARN] {msg}")
            return False

        # 4. Detect newly created window handle
        new_hwnd = self._find_new_window(
            self._before_hwnds, timeout=self.config.window_find_timeout
        )

        if not new_hwnd:
            msg = f"Explorer window for workspace {resolved_path} not detected within timeout"
            if self.config.strict_mode:
                raise ExplorerWindowNotFoundError(msg)
            print(f"[WARN] {msg}")
            return False

        self._controlled_hwnd = new_hwnd

        # 5. Bring Explorer window to foreground
        self._activate_window(new_hwnd)

        # 6. Keep open for configured duration
        if duration > 0:
            time.sleep(duration)

        # 7. Close ONLY the automation-controlled window
        self.close_controlled_window()
        return True

    # ------------------------------------------------------------
    # Cycle 2: Select Report File
    # ------------------------------------------------------------

    def select_report_file(
        self,
        project_path: str | Path,
        report_path: str | Path,
        display_duration: Optional[float] = None,
    ) -> bool:
        """
        Open Windows File Explorer in the reports directory and visually select/highlight
        the expected report file WITHOUT opening, double-clicking, copying, or modifying it.

        Args:
            project_path: Base directory of the project.
            report_path: Path to report file (relative to project_path or absolute).
            display_duration: Seconds to display selection before closing.

        Returns:
            bool: True if completed successfully.
        """
        if not self.config.enabled:
            return True

        # 1. Resolve full path to report file
        p_path = Path(project_path)
        r_path = Path(report_path)

        if r_path.is_absolute():
            full_report_path = r_path.resolve()
        else:
            full_report_path = (p_path / r_path).resolve()

        # 2. Validate report file existence
        if not full_report_path.exists() or not full_report_path.is_file():
            raise ReportFileNotFoundError(
                f"Expected report file does not exist: {full_report_path}"
            )

        target_file_str = str(full_report_path)
        target_file_name = full_report_path.name
        duration = (
            display_duration
            if display_duration is not None
            else self.config.report_selection_display_duration
        )

        # 3. Capture existing Explorer windows before launch
        self._before_hwnds = get_cabinet_hwnds()

        # 4. Launch Explorer with native /select flag
        # Explorer /select,<path> opens parent folder and selects the file natively.
        try:
            subprocess.Popen(["explorer.exe", f"/select,{target_file_str}"])
        except Exception as exc:
            msg = f"Failed to launch Explorer with selection for {target_file_str}: {exc}"
            if self.config.strict_mode:
                raise ExplorerAutomationError(msg) from exc
            print(f"[WARN] {msg}")
            return False

        # 5. Detect newly created window handle
        new_hwnd = self._find_new_window(
            self._before_hwnds, timeout=self.config.window_find_timeout
        )

        if not new_hwnd:
            msg = f"Explorer window for report {target_file_str} not detected within timeout"
            if self.config.strict_mode:
                raise ExplorerWindowNotFoundError(msg)
            print(f"[WARN] {msg}")
            return False

        self._controlled_hwnd = new_hwnd

        # 6. Bring Explorer window to foreground
        self._activate_window(new_hwnd)

        # 7. Resilient UI Selection Verification (SELECT ONLY)
        # Verify via pywinauto UIA backend that the file is selected
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            win = desktop.window(handle=new_hwnd)

            # Give Explorer brief UI render time
            time.sleep(0.3)

            for item in win.descendants(control_type="ListItem"):
                item_name = (item.element_info.name or "").strip()
                if target_file_name.lower() in item_name.lower():
                    # If not yet selected, call UIA programmatic select
                    is_sel = False
                    try:
                        if hasattr(item, "is_selected"):
                            is_sel = bool(item.is_selected())
                        elif hasattr(item, "iface_selection_item"):
                            is_sel = bool(item.iface_selection_item.CurrentIsSelected)
                    except Exception:
                        pass

                    if not is_sel:
                        try:
                            # SelectionItemPattern.Select() selects without opening
                            if hasattr(item, "select"):
                                item.select()
                        except Exception:
                            pass
                    break
        except Exception as uia_err:
            # Native /select already selected the item; UIA is a verification helper
            pass

        # 8. Keep open for configured duration
        if duration > 0:
            time.sleep(duration)

        # 9. Close ONLY the automation-controlled window
        self.close_controlled_window()
        return True


# ============================================================
# PUBLIC CONVENIENCE FUNCTIONS
# ============================================================

def open_project_workspace(
    project_path: str | Path,
    display_duration: Optional[float] = None,
    config: Optional[ExplorerConfig] = None,
) -> bool:
    """
    High-level entry point to display the project workspace folder in Explorer.
    """
    automation = ExplorerAutomation(config=config)
    return automation.open_workspace(
        project_path=project_path,
        display_duration=display_duration,
    )


def select_report_file(
    project_path: str | Path,
    report_path: str | Path,
    display_duration: Optional[float] = None,
    config: Optional[ExplorerConfig] = None,
) -> bool:
    """
    High-level entry point to visually highlight/select a report file in Explorer.
    """
    automation = ExplorerAutomation(config=config)
    return automation.select_report_file(
        project_path=project_path,
        report_path=report_path,
        display_duration=display_duration,
    )
