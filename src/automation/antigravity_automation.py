import time
import json
import os
import ctypes

import pyautogui
import pyperclip
import psutil
import win32gui
import win32process
import win32con
import win32api

from .automation_interface import AutomationInterface
from .automation_result import AutomationResult


CACHE_PATH = os.path.join(
    os.path.dirname(__file__),
    "antigravity_process_cache.json"
)


class AntigravityAutomation(AutomationInterface):

    def __init__(self):
        self._cached_exe_name = self._load_cached_exe_name()

    # ---------- Persistence ----------

    def _load_cached_exe_name(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r") as file:
                    return json.load(file).get("exe_name")
            except Exception:
                return None

        return None

    def _save_cached_exe_name(self, exe_name):
        self._cached_exe_name = exe_name

        with open(CACHE_PATH, "w") as file:
            json.dump(
                {"exe_name": exe_name},
                file
            )

    # ---------- Window Detection ----------

    def _enum_visible_windows(self):
        results = []

        def callback(hwnd, _):

            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd).strip()

            if not title:
                return

            try:
                _, pid = (
                    win32process
                    .GetWindowThreadProcessId(hwnd)
                )

                exe_name = psutil.Process(pid).name()

                results.append(
                    (hwnd, title, exe_name)
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):
                return

        win32gui.EnumWindows(callback, None)

        return results

    def _find_antigravity_window(self):

        windows = self._enum_visible_windows()

        # Primary detection using process name
        if self._cached_exe_name:

            for hwnd, title, exe_name in windows:

                if (
                    exe_name.lower()
                    == self._cached_exe_name.lower()
                ):
                    return hwnd, title, exe_name

        # Bootstrap detection
        for hwnd, title, exe_name in windows:

            if title.lower() == "antigravity":

                self._save_cached_exe_name(
                    exe_name
                )

                return hwnd, title, exe_name

        return None

    # ---------- Foreground Verification ----------

    def _is_window_foreground(self, hwnd):

        return (
            win32gui.GetForegroundWindow()
            == hwnd
        )

    # ---------- Layered Window Activation ----------

    def _activate_window(self, hwnd):

        if win32gui.IsIconic(hwnd):

            win32gui.ShowWindow(
                hwnd,
                win32con.SW_RESTORE
            )

            time.sleep(0.2)

        if self._is_window_foreground(hwnd):
            return True

        def try_allow_foreground():

            try:
                _, pid = (
                    win32process
                    .GetWindowThreadProcessId(hwnd)
                )

                ctypes.windll.user32.AllowSetForegroundWindow(
                    pid
                )

                win32gui.SetForegroundWindow(hwnd)

            except Exception:
                pass

        def try_attach_thread():

            try:
                fg_hwnd = (
                    win32gui.GetForegroundWindow()
                )

                fg_thread = (
                    win32process
                    .GetWindowThreadProcessId(
                        fg_hwnd
                    )[0]
                )

                target_thread = (
                    win32process
                    .GetWindowThreadProcessId(
                        hwnd
                    )[0]
                )

                if fg_thread != target_thread:

                    win32process.AttachThreadInput(
                        fg_thread,
                        target_thread,
                        True
                    )

                    try:
                        win32gui.BringWindowToTop(
                            hwnd
                        )

                        win32gui.SetForegroundWindow(
                            hwnd
                        )

                    finally:
                        win32process.AttachThreadInput(
                            fg_thread,
                            target_thread,
                            False
                        )

                else:

                    win32gui.SetForegroundWindow(
                        hwnd
                    )

            except Exception:
                pass

        def try_alt_trick():

            try:
                win32api.keybd_event(
                    win32con.VK_MENU,
                    0,
                    0,
                    0
                )

                win32gui.SetForegroundWindow(
                    hwnd
                )

                win32api.keybd_event(
                    win32con.VK_MENU,
                    0,
                    win32con.KEYEVENTF_KEYUP,
                    0
                )

            except Exception:
                pass

        def try_topmost():

            try:
                flags = (
                    win32con.SWP_NOMOVE
                    | win32con.SWP_NOSIZE
                )

                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOPMOST,
                    0,
                    0,
                    0,
                    0,
                    flags
                )

                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_NOTOPMOST,
                    0,
                    0,
                    0,
                    0,
                    flags
                )

            except Exception:
                pass

        def try_click():

            try:
                left, top, right, bottom = (
                    win32gui.GetWindowRect(hwnd)
                )

                x = (
                    left
                    + (right - left) // 2
                )

                y = top + 40

                pyautogui.click(x, y)

            except Exception:
                pass

        strategies = [
            try_allow_foreground,
            try_attach_thread,
            try_alt_trick,
            try_topmost,
            try_click
        ]

        for strategy in strategies:

            for _ in range(3):

                strategy()

                time.sleep(0.2)

                if self._is_window_foreground(hwnd):
                    return True

        return False

    # ---------- Focus Chat Input ----------

    def _focus_chat_input(self, hwnd):
        """
        Click inside the Antigravity chat input area.
        Window focus alone does not guarantee text input focus.
        """

        try:
            left, top, right, bottom = (
                win32gui.GetWindowRect(hwnd)
            )

            width = right - left
            height = bottom - top

            # Bottom-center of window.
            # This should fall inside the chat input area.
            x = left + width // 2

            y = bottom - int(height * 0.08)

            pyautogui.click(x, y)

            time.sleep(0.5)

            return True

        except Exception:
            return False

    # ---------- Launch ----------

    def _open_antigravity(self):

        pyautogui.press("win")

        time.sleep(0.3)

        pyautogui.write(
            "Antigravity",
            interval=0.02
        )

        time.sleep(0.5)

        pyautogui.press("enter")

        # Wait dynamically for window
        for _ in range(30):

            time.sleep(0.5)

            found = (
                self._find_antigravity_window()
            )

            if found:
                return found

        return None

    # ---------- Main Execution ----------

    def execute(self, prompt):

        try:

            found = (
                self._find_antigravity_window()
            )

            # ==================================
            # ANTIGRAVITY NOT RUNNING
            # ==================================

            if not found:

                found = self._open_antigravity()

                if not found:

                    return AutomationResult(
                        success=False,
                        error=(
                            "Antigravity window "
                            "not found"
                        )
                    )

                hwnd, title, exe_name = found

                if not self._activate_window(hwnd):

                    return AutomationResult(
                        success=False,
                        error=(
                            "Could not bring "
                            "Antigravity to foreground"
                        )
                    )

                # Fresh application launch needs time
                # for UI and chat input to initialize
                time.sleep(10)

            # ==================================
            # ANTIGRAVITY ALREADY RUNNING
            # ==================================

            else:

                hwnd, title, exe_name = found

                if not self._activate_window(hwnd):

                    return AutomationResult(
                        success=False,
                        error=(
                            "Could not bring "
                            "Antigravity to foreground"
                        )
                    )

                # Already running -> minimal delay
                time.sleep(0.3)

            # ==================================
            # FINAL FOCUS CHECK
            # ==================================

            if not self._is_window_foreground(hwnd):

                return AutomationResult(
                    success=False,
                    error=(
                        "Antigravity lost foreground "
                        "focus before prompt"
                    )
                )

            # ==================================
            # FOCUS CHAT INPUT
            # ==================================

            focused = self._focus_chat_input(hwnd)

            if not focused:

                return AutomationResult(
                    success=False,
                    error=(
                        "Could not focus "
                        "Antigravity chat input"
                    )
                )

            # ==================================
            # COPY PROMPT
            # ==================================

            pyperclip.copy(prompt)

            time.sleep(0.2)

            # ==================================
            # PASTE PROMPT
            # ==================================

            pyautogui.hotkey(
                "ctrl",
                "v"
            )

            time.sleep(0.5)

            # ==================================
            # SEND PROMPT
            # ==================================

            pyautogui.press("enter")

            return AutomationResult(
                success=True,
                output=(
                    f"Antigravity ({exe_name}) "
                    "activated and prompt sent"
                )
            )

        except Exception as e:

            return AutomationResult(
                success=False,
                error=str(e)
            )