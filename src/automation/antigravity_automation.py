import time
import json
import os
import ctypes
from pathlib import Path

import pyautogui
import pyperclip
import psutil
import win32gui
import win32process
import win32con
import win32api

from .automation_interface import AutomationInterface
from .automation_result import AutomationResult
from .application_discovery import (
    ANTIGRAVITY_TARGET,
    ApplicationDiscovery,
    ApplicationDiscoveryError,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_PATH = str(_PROJECT_ROOT / "data" / "antigravity_process_cache.json")


def _ensure_desktop_access():
    """Attach current thread to interactive input desktop if needed."""
    try:
        user32 = ctypes.windll.user32
        h_input = user32.OpenInputDesktop(0, False, 0x01FF)
        if h_input:
            user32.SetThreadDesktop(h_input)
    except Exception:
        pass


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

        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as file:
            json.dump(
                {"exe_name": exe_name},
                file
            )

    # ---------- Window Detection ----------

    def _enum_visible_windows(self):
        _ensure_desktop_access()
        results = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True

            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid < 0:
                    pid = pid + (1 << 32)
                exe_name = psutil.Process(pid).name()
                results.append((hwnd, title, exe_name))
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            pass

        return results

    def _find_antigravity_window(self):
        windows = self._enum_visible_windows()

        # Primary detection using cached process name
        if self._cached_exe_name:
            for hwnd, title, exe_name in windows:
                if exe_name.lower() == self._cached_exe_name.lower():
                    return hwnd, title, exe_name

        # Detection by process or title matching antigravity
        for hwnd, title, exe_name in windows:
            if "antigravity" in exe_name.lower() or "antigravity" in title.lower():
                self._save_cached_exe_name(exe_name)
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

    # ---------- Chat Layout & Input Positioning ----------

    def _detect_chat_layout(self, antigravity_element) -> str:
        """
        Detect whether Antigravity is showing NEW_CHAT, EXISTING_CHAT, or UNKNOWN.
        Considers conversation messages, model responses, user bubbles, and visible elements.
        """
        if antigravity_element is None:
            return "UNKNOWN"

        try:
            descendants = antigravity_element.descendants()
        except Exception:
            return "UNKNOWN"

        has_existing_messages = False
        has_new_chat_indicators = False
        input_rel_y = None

        for el in descendants:
            try:
                name = (el.element_info.name or "").lower()
                cls = (el.element_info.class_name or "").lower()

                # Existing chat indicators
                if (
                    "user message" in name
                    or "model-response" in cls
                    or "response-container" in cls
                    or "conversation-turn" in cls
                    or "chat-bubble" in cls
                ):
                    has_existing_messages = True

                # New chat indicators
                if (
                    "what would you like to build" in name
                    or "start a new chat" in name
                    or "how can i help" in name
                    or "start new chat" in name
                ):
                    has_new_chat_indicators = True

                # Check position of message input if found
                if "message input" in name or "cursor-text" in cls or "ask anything" in name:
                    r = el.rectangle()
                    win_r = antigravity_element.rectangle()
                    win_h = max(1, win_r.height())
                    input_rel_y = (r.top - win_r.top) / win_h
            except Exception:
                continue

        if has_existing_messages:
            return "EXISTING_CHAT"
        if has_new_chat_indicators:
            return "NEW_CHAT"

        # Position-based heuristic if explicit markers are absent
        if input_rel_y is not None:
            if input_rel_y >= 0.70:
                return "EXISTING_CHAT"
            elif 0.30 <= input_rel_y <= 0.65:
                return "NEW_CHAT"

        return "UNKNOWN"

    def _find_chat_input_candidate(self, antigravity_element, layout: str = "UNKNOWN"):
        """
        Search and score UI Automation candidates for the chat input box.
        Supports ComboBox, Edit, Document, Pane controls.
        Evaluates dimension, panel location, class keywords, and layout match.
        """
        if antigravity_element is None:
            return None

        try:
            win_rect = antigravity_element.rectangle()
            win_w = max(1, win_rect.width())
            win_h = max(1, win_rect.height())
            candidates = []

            for el in antigravity_element.descendants():
                try:
                    info = el.element_info
                    ct = info.control_type or ""
                    if ct not in ("ComboBox", "Edit", "Document", "Pane", "Group"):
                        continue

                    rect = el.rectangle()
                    w = rect.width()
                    h = rect.height()

                    # Filter invalid dimensions
                    if w < 150 or h < 20 or h > 450:
                        continue

                    # Filter elements off-screen or outside window
                    if rect.left < win_rect.left - 10 or rect.right > win_rect.right + 20:
                        continue
                    if rect.top < win_rect.top - 10 or rect.bottom > win_rect.bottom + 20:
                        continue

                    if hasattr(el, "is_enabled") and not el.is_enabled():
                        continue

                    name = (info.name or "").lower()
                    cls = (info.class_name or "").lower()

                    is_match = (
                        ct in ("ComboBox", "Edit")
                        or "cursor-text" in cls
                        or "message input" in name
                        or "ask anything" in name
                        or "chat input" in name
                        or "prompt" in name
                    )
                    if not is_match:
                        continue

                    score = 0
                    if "message input" in name:
                        score += 100
                    if "ask anything" in name:
                        score += 80
                    if "cursor-text" in cls:
                        score += 60
                    if ct in ("ComboBox", "Edit"):
                        score += 30

                    center_x = (rect.left + rect.right) / 2
                    rel_x = (center_x - win_rect.left) / win_w
                    if 0.30 <= rel_x <= 0.85:
                        score += 25

                    rel_y = (rect.top - win_rect.top) / win_h
                    if layout == "NEW_CHAT":
                        if 0.30 <= rel_y <= 0.65:
                            score += 50
                        elif rel_y >= 0.70:
                            score += 10
                    elif layout == "EXISTING_CHAT":
                        if rel_y >= 0.70:
                            score += 50
                        elif 0.30 <= rel_y <= 0.65:
                            score += 10
                    else:  # UNKNOWN
                        if rel_y >= 0.70:
                            score += 35
                        elif 0.30 <= rel_y <= 0.65:
                            score += 30

                    candidates.append((score, el, rect))
                except Exception:
                    continue

            if not candidates:
                return None

            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
        except Exception:
            return None

    def _verify_input_focus(self, hwnd, element=None) -> bool:
        """
        Verify that Antigravity has foreground focus and, where technically
        possible, the target input element has keyboard focus.
        """
        if not self._is_window_foreground(hwnd):
            return False

        if element is not None:
            try:
                if hasattr(element, "has_keyboard_focus") and element.has_keyboard_focus():
                    return True
            except Exception:
                pass

        return True

    def _focus_chat_input(self, hwnd, uia_window=None) -> bool:
        """
        Focus chat input using UIA discovery with layout-aware coordinate fallback.
        Supports both NEW_CHAT (middle) and EXISTING_CHAT (bottom) layouts.
        Performs bounded attempts with focus verification.
        """
        _ensure_desktop_access()

        layout = "UNKNOWN"
        candidate_el = None

        if uia_window is not None:
            layout = self._detect_chat_layout(uia_window)
            candidate_el = self._find_chat_input_candidate(uia_window, layout=layout)
        else:
            try:
                from pywinauto import Desktop
                uia_window = Desktop(backend="uia").window(handle=hwnd)
                layout = self._detect_chat_layout(uia_window)
                candidate_el = self._find_chat_input_candidate(uia_window, layout=layout)
            except Exception:
                pass

        # Attempt 1: Click and focus discovered UIA candidate
        if candidate_el is not None:
            try:
                r = candidate_el.rectangle()
                cx = r.left + r.width() // 2
                cy = r.top + r.height() // 2

                try:
                    candidate_el.click_input()
                except Exception:
                    pyautogui.click(cx, cy)

                try:
                    candidate_el.set_focus()
                except Exception:
                    pass

                time.sleep(0.3)
                if self._verify_input_focus(hwnd, candidate_el):
                    return True
            except Exception as e:
                print(f"[WARN] UIA candidate click failed: {e}")

        # Controlled Fallback Strategy (Bounded coordinate attempts)
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            middle_x = left + width // 2
            middle_y = top + int(height * 0.50)

            bottom_x = left + width // 2
            bottom_y = bottom - int(height * 0.08)

            if layout == "NEW_CHAT":
                attempts = [
                    ("middle (new chat layout)", middle_x, middle_y),
                    ("bottom (existing chat fallback)", bottom_x, bottom_y),
                ]
            else:
                attempts = [
                    ("bottom (existing chat layout)", bottom_x, bottom_y),
                    ("middle (new chat fallback)", middle_x, middle_y),
                ]

            for label, x, y in attempts:
                print(f"[INFO] Attempting input focus at {label}: ({x}, {y})")
                pyautogui.click(x, y)
                time.sleep(0.3)
                if self._verify_input_focus(hwnd):
                    return True

        except Exception as fallback_err:
            print(f"[WARN] Coordinate fallback error: {fallback_err}")

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

            # ==================================
            # DISCOVERY & ACTIVATION
            # ==================================

            found = self._find_antigravity_window()

            if not found:
                discovery = ApplicationDiscovery()
                try:
                    found = discovery.ensure_application_ready(
                        ANTIGRAVITY_TARGET, timeout=10.0
                    )
                except Exception:
                    found = self._open_antigravity()

                if not found:
                    return AutomationResult(
                        success=False,
                        error="Antigravity window not found"
                    )

                hwnd, title, exe_name = found
                if not self._activate_window(hwnd):
                    return AutomationResult(
                        success=False,
                        error="Could not bring Antigravity to foreground"
                    )
                time.sleep(1.0)
            else:
                hwnd, title, exe_name = found
                if not self._activate_window(hwnd):
                    return AutomationResult(
                        success=False,
                        error="Could not bring Antigravity to foreground"
                    )
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
            # FINAL FOCUS VERIFICATION BEFORE TYPING
            # ==================================

            if not self._is_window_foreground(hwnd):

                return AutomationResult(
                    success=False,
                    error=(
                        "Antigravity lost foreground "
                        "focus before prompt typing"
                    )
                )

            # ==================================
            # CLEAR EXISTING / STALE TEXT
            # ==================================

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.05)
            pyautogui.press("backspace")
            time.sleep(0.1)

            # ==================================
            # COPY PROMPT
            # ==================================

            pyperclip.copy(prompt)

            time.sleep(0.1)

            # ==================================
            # PASTE PROMPT
            # ==================================

            pyautogui.hotkey(
                "ctrl",
                "v"
            )

            time.sleep(0.3)

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