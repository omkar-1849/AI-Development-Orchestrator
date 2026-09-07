import ctypes
import time
from typing import Optional

import win32gui
from pywinauto import Desktop

from src.automation.claude_sender import (
    _ensure_desktop_access,
    find_input_box,
    send_prompt,
)


def find_claude(timeout: float = 10.0):
    """
    Locate and focus the Claude Desktop window.
    Supports both direct HWND finding and pywinauto UIA desktop search.
    Restores the window if minimized and brings it to the foreground.
    """
    _ensure_desktop_access()
    desktop = Desktop(backend="uia")

    print("Searching for Claude window...")

    start_time = time.time()
    user32 = ctypes.windll.user32

    while time.time() - start_time < timeout:
        # Method 1: Direct Win32 FindWindow for instant HWND discovery
        hwnd = win32gui.FindWindow("Chrome_WidgetWin_1", "Claude")

        # Method 1b: Search by class/title if exact title changed
        if not hwnd:
            def _enum_cb(h, acc):
                if win32gui.IsWindowVisible(h):
                    title = win32gui.GetWindowText(h)
                    cls = win32gui.GetClassName(h)
                    if ("claude" in title.lower() or title == "Claude") and cls == "Chrome_WidgetWin_1":
                        acc.append(h)

            candidates = []
            try:
                win32gui.EnumWindows(_enum_cb, candidates)
                if candidates:
                    hwnd = candidates[0]
            except Exception:
                pass

        if hwnd:
            try:
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    time.sleep(0.3)
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.3)

                claude = desktop.window(handle=hwnd)
                print("Claude window found")
                try:
                    claude.set_focus()
                except Exception:
                    pass
                return claude
            except Exception:
                pass

        # Method 2: pywinauto UIA window search
        try:
            claude = desktop.window(title="Claude")
            if claude.exists(timeout=0.5):
                print("Claude window found")
                try:
                    wrapper = claude.wrapper_object()
                    h = wrapper.handle
                    if user32.IsIconic(h):
                        user32.ShowWindow(h, 9)
                        time.sleep(0.3)
                    user32.SetForegroundWindow(h)
                    wrapper.set_focus()
                except Exception:
                    pass
                return claude
        except Exception:
            pass

        time.sleep(0.5)

    print("FAILED: Claude window not found: timed out")
    return None