import ctypes
import time
from typing import Optional

import pyperclip
from pywinauto.keyboard import send_keys


def _ensure_desktop_access():
    """Attach current thread to the interactive input desktop if needed."""
    try:
        user32 = ctypes.windll.user32
        h_input = user32.OpenInputDesktop(0, False, 0x01FF)
        if h_input:
            user32.SetThreadDesktop(h_input)
    except Exception:
        pass


def _ensure_window_active(claude):
    """Restore and bring Claude window to the foreground."""
    try:
        wrapper = claude.wrapper_object() if hasattr(claude, "wrapper_object") else claude
        hwnd = getattr(wrapper, "handle", None)
        if hwnd:
            user32 = ctypes.windll.user32
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.3)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.2)
    except Exception:
        pass


def _is_valid_input_element(element) -> bool:
    """Validate that the candidate element is visible on screen with positive dimensions."""
    try:
        rect = element.rectangle()
        if rect.width() < 50 or rect.height() < 10:
            return False
        if hasattr(element, "is_enabled") and not element.is_enabled():
            return False
        return True
    except Exception:
        return False


def find_input_box(claude, timeout: float = 10.0, poll_interval: float = 0.5):
    """
    Find Claude's prompt input box using a resilient multi-tiered strategy.

    Tier 1 (ProseMirror / TipTap):
        Claude Desktop uses ProseMirror contenteditable editor.
        Matches Edit or Document controls with class containing 'prosemirror' or 'tiptap'.
    Tier 2 (Prompt Placeholder):
        Matches Edit or Document controls with known placeholder text:
        'Write your prompt to Claude', 'Reply to Claude', 'Message Claude', etc.
    Tier 3 (Document Control):
        Matches Document controls (Chromium role mapping) with ProseMirror or placeholder name.
    Tier 4 (Structural Edit):
        Directly queries control_type='Edit' descendants for a primary visible control.
    Tier 5 (Fallback traversal):
        Broader scan across descendants if direct queries fail.
    """
    _ensure_desktop_access()
    print("Searching for Claude input...")

    _ensure_window_active(claude)

    # Resolve wrapper once to avoid re-searching on every query
    try:
        claude_obj = claude.wrapper_object() if hasattr(claude, "wrapper_object") else claude
    except Exception:
        claude_obj = claude

    start_time = time.time()
    known_name_patterns = (
        "write your prompt",
        "reply to claude",
        "prompt to claude",
        "message claude",
        "how can claude help",
        "ask claude",
    )

    while True:
        # Tier 1: Search control_type='Edit' with ProseMirror / TipTap class
        try:
            for el in claude_obj.descendants(control_type="Edit"):
                info = el.element_info
                cls_name = (info.class_name or "").lower()
                if ("prosemirror" in cls_name or "tiptap" in cls_name) and _is_valid_input_element(el):
                    print(f"Claude input found (ProseMirror Edit: {info.class_name!r}).")
                    return el
        except Exception:
            pass

        # Tier 2: Search control_type='Edit' with known placeholder names
        try:
            for el in claude_obj.descendants(control_type="Edit"):
                name = (el.element_info.name or "").strip().lower()
                if any(p in name for p in known_name_patterns) and _is_valid_input_element(el):
                    print(f"Claude input found (Name pattern: {el.element_info.name!r}).")
                    return el
        except Exception:
            pass

        # Tier 3: Search control_type='Document' (Chromium role mapping)
        try:
            for el in claude_obj.descendants(control_type="Document"):
                info = el.element_info
                cls_name = (info.class_name or "").lower()
                name = (info.name or "").strip().lower()
                if (
                    "prosemirror" in cls_name
                    or "tiptap" in cls_name
                    or any(p in name for p in known_name_patterns)
                ) and _is_valid_input_element(el):
                    print(f"Claude input found (Document control: {info.name!r}).")
                    return el
        except Exception:
            pass

        # Tier 4: Single visible, enabled Edit control
        try:
            edits = [
                el for el in claude_obj.descendants(control_type="Edit")
                if _is_valid_input_element(el)
            ]
            if len(edits) == 1:
                el = edits[0]
                print(f"Claude input found (Single primary Edit: {el.element_info.name!r}).")
                return el
            elif len(edits) > 1:
                # Select the lowest on screen (input box is at bottom of chat)
                edits.sort(key=lambda e: (e.rectangle().top, e.rectangle().width()), reverse=True)
                el = edits[0]
                print(f"Claude input found (Bottom Edit control: {el.element_info.name!r}).")
                return el
        except Exception:
            pass

        # Tier 5: Fallback scan of all descendants
        try:
            for el in claude_obj.descendants():
                try:
                    info = el.element_info
                    ctype = info.control_type or ""
                    cls_name = (info.class_name or "").lower()
                    name = (info.name or "").strip().lower()

                    if ctype in ("Edit", "Document") and (
                        "prosemirror" in cls_name
                        or "tiptap" in cls_name
                        or any(p in name for p in known_name_patterns)
                    ) and _is_valid_input_element(el):
                        print(f"Claude input found (Fallback scan: {info.name!r}).")
                        return el
                except Exception:
                    continue
        except Exception:
            pass

        if time.time() - start_time >= timeout:
            break

        time.sleep(poll_interval)

    print("FAILED: Claude input not found")
    return None


def send_prompt(claude, prompt: str, timeout: float = 10.0):
    """
    Insert and send a prompt to Claude.

    Uses clipboard paste instead of type_keys so that
    JSON, brackets, quotes, multiline prompts, and special
    characters are handled safely.
    """
    _ensure_desktop_access()

    input_box = find_input_box(claude, timeout=timeout)

    if input_box is None:
        raise RuntimeError("Claude input box not found")

    # Focus Claude window & input box
    try:
        claude.set_focus()
    except Exception:
        pass

    try:
        input_box.click_input()
    except Exception:
        pass

    try:
        input_box.set_focus()
    except Exception:
        pass

    time.sleep(0.5)

    # Copy full prompt to clipboard
    pyperclip.copy(prompt)

    # Paste safely
    send_keys("^v")

    time.sleep(0.5)

    # Send prompt
    send_keys("{ENTER}")

    print("Prompt sent successfully.")