import ctypes
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _ensure_desktop_access():
    """Ensure current thread is attached to the user's interactive desktop."""
    try:
        user32 = ctypes.windll.user32
        h_input = user32.OpenInputDesktop(0, False, 0x01FF)
        if h_input:
            user32.SetThreadDesktop(h_input)
    except Exception:
        pass


_ensure_desktop_access()

from pywinauto import Desktop


def inspect_claude_ui(max_depth: Optional[int] = None):
    _ensure_desktop_access()
    desktop = Desktop(backend="uia")

    print("Searching for Claude window...")
    try:
        import win32gui
        hwnd = win32gui.FindWindow("Chrome_WidgetWin_1", "Claude")
        if hwnd:
            user32 = ctypes.windll.user32
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)
                time.sleep(0.3)
            user32.SetForegroundWindow(hwnd)
            claude_wrapper = desktop.window(handle=hwnd).wrapper_object()
        else:
            claude = desktop.window(title="Claude")
            claude.wait("exists ready", timeout=10)
            claude_wrapper = claude.wrapper_object()
    except Exception as exc:
        print(f"FAILED to find Claude window: {exc}")
        return

    hwnd = claude_wrapper.handle
    user32 = ctypes.windll.user32
    if user32.IsIconic(hwnd):
        print("Claude is minimized. Restoring window...")
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.5)

    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    rect = claude_wrapper.rectangle()
    print(f"\n==========================================")
    print(f"CLAUDE WINDOW INSPECTION")
    print(f"==========================================")
    print(f"Title:        {claude_wrapper.window_text()!r}")
    print(f"HWND:         {hwnd}")
    print(f"Class:        {claude_wrapper.class_name()!r}")
    print(f"Rectangle:    {rect}")
    print(f"Is Visible:   {claude_wrapper.is_visible()}")
    print(f"==========================================\n")

    input_candidates = []
    buttons = []
    response_markers = []

    print(f"{'#':<4} {'Type':<12} {'Name':<35} {'Class':<30} {'AutoID':<15} {'Rect'}")
    print("-" * 120)

    for i, element in enumerate(claude_wrapper.descendants()):
        try:
            info = element.element_info
            ctype = info.control_type or ""
            name = (info.name or "").strip()
            cname = info.class_name or ""
            autoid = info.automation_id or ""
            framework_id = getattr(info, "framework_id", "")
            elem_rect = element.rectangle()
            is_visible = element.is_visible()

            # Classify candidate inputs
            cname_lower = cname.lower()
            name_lower = name.lower()
            is_input = (
                (ctype in ("Edit", "Document") and ("prosemirror" in cname_lower or "tiptap" in cname_lower))
                or (ctype == "Edit" and ("write your prompt" in name_lower or "reply to claude" in name_lower))
                or (ctype == "Edit" and elem_rect.width() > 100 and elem_rect.height() > 15)
            )

            if is_input:
                input_candidates.append((i, ctype, name, cname, autoid, elem_rect))

            if ctype == "Button" and name:
                buttons.append((i, name, cname, autoid))

            if name.startswith("Claude responded:"):
                response_markers.append((i, name, elem_rect))

            name_disp = (name[:32] + "...") if len(name) > 35 else name
            cname_disp = (cname[:27] + "...") if len(cname) > 30 else cname
            autoid_disp = (autoid[:12] + "...") if len(autoid) > 15 else autoid
            marker = " [INPUT CANDIDATE]" if is_input else ""

            print(
                f"[{i:03d}] {ctype:<12} {name_disp:<35} {cname_disp:<30} {autoid_disp:<15} {elem_rect}{marker}"
            )

        except Exception as e:
            continue

    print(f"\n==========================================")
    print(f"SUMMARY OF KEY AUTOMATION TARGETS")
    print(f"==========================================")
    print(f"\nFound {len(input_candidates)} Candidate Input Box(es):")
    for idx, ctype, name, cname, autoid, r in input_candidates:
        print(f"  - Index [{idx}]: ControlType={ctype}, Name={name!r}, Class={cname!r}, AutoID={autoid!r}, Rect={r}")

    print(f"\nFound {len(response_markers)} Response Marker(s):")
    for idx, name, r in response_markers:
        print(f"  - Index [{idx}]: Name={name[:60]!r}, Rect={r}")

    print(f"\nFound {len(buttons)} Interactive Button(s):")
    for idx, name, cname, autoid in buttons[:10]:
        print(f"  - Index [{idx}]: Name={name!r}, Class={cname!r}")
    if len(buttons) > 10:
        print(f"  ... and {len(buttons) - 10} more buttons.")

    print(f"==========================================\n")


def main():
    inspect_claude_ui()


if __name__ == "__main__":
    main()
