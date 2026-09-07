import ctypes
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import psutil
import win32api
import win32con
import win32gui
import win32process


# =====================================================================
# EXCEPTIONS
# =====================================================================

class ApplicationDiscoveryError(Exception):
    """Base exception for application discovery and lifecycle failures."""
    pass


class ApplicationNotFoundError(ApplicationDiscoveryError):
    """Raised when an application window or process cannot be located."""
    pass


class ApplicationLaunchError(ApplicationDiscoveryError):
    """Raised when an application process cannot be launched."""
    pass


class ApplicationStartupTimeoutError(ApplicationDiscoveryError):
    """Raised when launched application fails to display a visible window in time."""
    pass


class ApplicationActivationError(ApplicationDiscoveryError):
    """Raised when an application window cannot be activated / brought to front."""
    pass


class ApplicationFocusError(ApplicationDiscoveryError):
    """Raised when foreground focus cannot be verified on the target window."""
    pass


# =====================================================================
# TARGET CONFIGURATION
# =====================================================================

@dataclass
class ApplicationTarget:
    name: str
    window_title_patterns: List[str] = field(default_factory=list)
    process_patterns: List[str] = field(default_factory=list)
    window_classes: List[str] = field(default_factory=list)
    launch_commands: List[str] = field(default_factory=list)
    env_path_var: Optional[str] = None
    default_exe_names: List[str] = field(default_factory=list)


# Predefined targets
CLAUDE_TARGET = ApplicationTarget(
    name="Claude",
    window_title_patterns=["claude", "claude desktop"],
    process_patterns=["claude.exe", "claude"],
    window_classes=["Chrome_WidgetWin_1"],
    launch_commands=["Claude", "claude"],
    env_path_var="CLAUDE_APP_PATH",
    default_exe_names=["Claude.exe"],
)

ANTIGRAVITY_TARGET = ApplicationTarget(
    name="Antigravity",
    window_title_patterns=["antigravity"],
    process_patterns=["antigravity.exe", "antigravity"],
    window_classes=["Chrome_WidgetWin_1"],
    launch_commands=["Antigravity", "antigravity"],
    env_path_var="ANTIGRAVITY_APP_PATH",
    default_exe_names=["Antigravity.exe"],
)


# =====================================================================
# DESKTOP ACCESS HELPER
# =====================================================================

def ensure_desktop_access() -> None:
    """Attach current thread to interactive input desktop if needed."""
    try:
        user32 = ctypes.windll.user32
        h_input = user32.OpenInputDesktop(0, False, 0x01FF)
        if h_input:
            user32.SetThreadDesktop(h_input)
    except Exception:
        pass


# =====================================================================
# APPLICATION DISCOVERY ENGINE
# =====================================================================

class ApplicationDiscovery:
    """
    Reusable application discovery, launch, window activation,
    foreground verification, and readiness layer for desktop applications.
    """

    def __init__(
        self,
        discovery_timeout: float = 5.0,
        startup_timeout: float = 15.0,
        activation_retries: int = 3,
    ):
        self.discovery_timeout = float(
            os.environ.get("APP_DISCOVERY_TIMEOUT", discovery_timeout)
        )
        self.startup_timeout = float(
            os.environ.get("APP_STARTUP_TIMEOUT", startup_timeout)
        )
        self.activation_retries = int(
            os.environ.get("APP_ACTIVATION_RETRIES", activation_retries)
        )

    # ---------- Enumerate Windows ----------

    def enumerate_visible_windows(self) -> List[Tuple[int, str, str, str]]:
        """
        Enumerate all visible top-level windows.
        Returns list of (hwnd, title, exe_name, class_name).
        Guarantees callback returns True to continue full enumeration.
        """
        ensure_desktop_access()
        results: List[Tuple[int, str, str, str]] = []

        def callback(hwnd: int, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True

            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True

            cls_name = win32gui.GetClassName(hwnd)

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid < 0:
                    pid = pid + (1 << 32)
                exe_name = psutil.Process(pid).name()
                results.append((hwnd, title, exe_name, cls_name))
            except Exception:
                pass

            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            pass

        return results

    # ---------- Find Window ----------

    def find_visible_window(
        self, target: ApplicationTarget
    ) -> Optional[Tuple[int, str, str]]:
        """
        Locate a visible window matching target title, process, or class patterns.
        Returns (hwnd, title, exe_name) or None.
        """
        windows = self.enumerate_visible_windows()

        # Phase 1: Process name matching
        if target.process_patterns:
            for hwnd, title, exe_name, cls in windows:
                exe_lower = exe_name.lower()
                for pat in target.process_patterns:
                    if pat.lower() in exe_lower or exe_lower == pat.lower():
                        return hwnd, title, exe_name

        # Phase 2: Title matching
        if target.window_title_patterns:
            for hwnd, title, exe_name, cls in windows:
                title_lower = title.lower()
                for pat in target.window_title_patterns:
                    if pat.lower() in title_lower:
                        return hwnd, title, exe_name

        return None

    # ---------- Find Process ----------

    def find_process(self, target: ApplicationTarget) -> Optional[psutil.Process]:
        """Check if any process matching target process_patterns is currently running."""
        patterns = [p.lower() for p in target.process_patterns]
        for proc in psutil.process_iter(attrs=["name", "pid"]):
            try:
                pname = (proc.info.get("name") or "").lower()
                for pat in patterns:
                    if pat in pname:
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    # ---------- Launch Application ----------

    def launch_application(self, target: ApplicationTarget) -> bool:
        """
        Attempt to launch the application using configured paths, known locations,
        or system search. Returns True if launch command was initiated.
        """
        # 1. Environment variable override
        if target.env_path_var:
            env_path = os.environ.get(target.env_path_var)
            if env_path and os.path.exists(env_path):
                try:
                    subprocess.Popen([env_path], close_fds=True)
                    return True
                except Exception as e:
                    print(f"[WARN] Launch via {target.env_path_var} failed: {e}")

        # 2. Known Windows user installation locations
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        app_data = os.environ.get("APPDATA", "")
        search_dirs = [
            Path(local_app_data) / "Programs" / target.name.lower(),
            Path(local_app_data) / "Programs" / target.name,
            Path(app_data) / target.name,
            Path(local_app_data) / target.name,
        ]

        for sdir in search_dirs:
            for exe in target.default_exe_names:
                candidate = sdir / exe
                if candidate.exists():
                    try:
                        subprocess.Popen([str(candidate)], close_fds=True)
                        return True
                    except Exception as e:
                        print(f"[WARN] Launch from {candidate} failed: {e}")

        # 3. Path / which check
        for exe in target.default_exe_names:
            resolved = shutil.which(exe)
            if resolved:
                try:
                    subprocess.Popen([resolved], close_fds=True)
                    return True
                except Exception:
                    pass

        # 4. Windows shell start command (handles start-menu shortcuts & protocol associations)
        for cmd in target.launch_commands:
            try:
                subprocess.Popen(
                    f'start "" "{cmd}"',
                    shell=True,
                    close_fds=True,
                )
                return True
            except Exception:
                pass

        return False

    # ---------- Wait For Window ----------

    def wait_for_window(
        self, target: ApplicationTarget, timeout: Optional[float] = None
    ) -> Tuple[int, str, str]:
        """
        Poll for a matching visible window up to timeout seconds.
        Raises ApplicationStartupTimeoutError on timeout.
        """
        limit = timeout if timeout is not None else self.startup_timeout
        start_time = time.time()
        poll_interval = 0.5

        while time.time() - start_time < limit:
            found = self.find_visible_window(target)
            if found:
                return found
            time.sleep(poll_interval)

        # Build diagnostic info on failure
        proc = self.find_process(target)
        proc_status = f"Process running (PID {proc.pid})" if proc else "Process NOT found"
        raise ApplicationStartupTimeoutError(
            f"Timed out ({limit}s) waiting for visible window of target '{target.name}'. "
            f"Diagnostics: {proc_status}; Launch was attempted; No visible matching window detected."
        )

    # ---------- Restore Window ----------

    def restore_window(self, hwnd: int) -> bool:
        """Restore window if iconic/minimized."""
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)
            return True
        except Exception:
            return False

    # ---------- Verify Foreground ----------

    def verify_foreground(self, hwnd: int) -> bool:
        """Return True if hwnd is the current foreground window."""
        return win32gui.GetForegroundWindow() == hwnd

    # ---------- Activate Window ----------

    def activate_window(self, hwnd: int, retries: Optional[int] = None) -> bool:
        """
        Bring window to foreground using layered activation strategies.
        Returns True if window is confirmed in foreground.
        """
        ensure_desktop_access()
        self.restore_window(hwnd)

        if self.verify_foreground(hwnd):
            return True

        max_attempts = retries if retries is not None else self.activation_retries

        # Layer 1: AllowSetForegroundWindow
        def try_allow_set_foreground():
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                ctypes.windll.user32.AllowSetForegroundWindow(pid)
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

        # Layer 2: AttachThreadInput
        def try_attach_thread():
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
                    win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

        # Layer 3: ALT trick
        def try_alt_trick():
            try:
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                win32gui.SetForegroundWindow(hwnd)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            except Exception:
                pass

        # Layer 4: TopMost toggle
        def try_topmost():
            try:
                flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            except Exception:
                pass

        # Layer 5: Click window title bar
        def try_title_click():
            try:
                import pyautogui
                l, t, r, b = win32gui.GetWindowRect(hwnd)
                cx = l + (r - l) // 2
                cy = t + 25
                pyautogui.click(cx, cy)
            except Exception:
                pass

        strategies = [
            try_allow_set_foreground,
            try_attach_thread,
            try_alt_trick,
            try_topmost,
            try_title_click,
        ]

        for attempt in range(max_attempts):
            for strat in strategies:
                strat()
                time.sleep(0.15)
                if self.verify_foreground(hwnd):
                    return True

        return False

    # ---------- Ensure Application Ready ----------

    def ensure_application_ready(
        self, target: ApplicationTarget, timeout: Optional[float] = None
    ) -> Tuple[int, str, str]:
        """
        Master discovery, launch, restoration, activation, and readiness lifecycle.
        1. Discover existing visible window.
        2. If absent, launch application and wait for visible window.
        3. Restore and activate window.
        4. Verify foreground readiness.
        Returns (hwnd, title, exe_name).
        Raises appropriate ApplicationDiscoveryError subclasses on failure.
        """
        ensure_desktop_access()

        # Step 1: Discover existing visible window
        found = self.find_visible_window(target)

        # Step 2: If not found, attempt launch
        if not found:
            launched = self.launch_application(target)
            if not launched:
                raise ApplicationLaunchError(
                    f"Could not launch '{target.name}': no valid executable path or launch command found."
                )

            # Wait for visible window after launch
            found = self.wait_for_window(target, timeout=timeout)

        hwnd, title, exe_name = found

        # Step 3: Restore & Activate
        self.restore_window(hwnd)
        activated = self.activate_window(hwnd)
        if not activated:
            raise ApplicationActivationError(
                f"Failed to activate window for '{target.name}' (HWND: {hwnd}, Title: '{title}')."
            )

        # Step 4: Verify foreground
        if not self.verify_foreground(hwnd):
            raise ApplicationFocusError(
                f"Target window for '{target.name}' (HWND: {hwnd}) did not achieve foreground focus."
            )

        return hwnd, title, exe_name
