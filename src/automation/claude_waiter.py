import time
from src.automation.claude_sender import _ensure_desktop_access


def is_generating(claude) -> bool:
    """
    Returns True when Claude is actively generating.
    """
    _ensure_desktop_access()

    # Fast path: query Button controls directly
    try:
        for element in claude.descendants(control_type="Button"):
            try:
                info = element.element_info
                name = (info.name or "").strip()
                if name == "Stop response" or "stop response" in name.lower():
                    return True
            except Exception:
                continue
    except Exception:
        pass

    # Fallback: general scan
    try:
        for element in claude.descendants():
            try:
                info = element.element_info
                if info.control_type == "Button" and "stop response" in (info.name or "").lower():
                    return True
            except Exception:
                continue
    except Exception:
        pass

    return False


def wait_for_response(
    claude,
    start_timeout: float = 15.0,
    completion_timeout: float = 300.0,
    poll_interval: float = 0.5,
) -> bool:
    """
    Wait for Claude generation lifecycle:
    idle -> generation starts (Stop response appears) -> generation finishes (Stop response disappears)
    """
    _ensure_desktop_access()
    print("Waiting for Claude generation to start...")

    start_time = time.time()

    # Phase 1: Wait for generation to begin
    while True:
        if is_generating(claude):
            print("Claude generation detected.")
            break

        if time.time() - start_time > start_timeout:
            raise TimeoutError(
                "Claude did not start generating within timeout."
            )

        time.sleep(poll_interval)

    print("Waiting for Claude response to finish...")

    completion_start = time.time()

    # Phase 2: Wait for generation to finish
    while True:
        if not is_generating(claude):
            print("Claude generation finished.")
            break

        if time.time() - completion_start > completion_timeout:
            raise TimeoutError(
                "Claude response did not finish within timeout."
            )

        time.sleep(poll_interval)

    # Small UI stabilization delay
    time.sleep(1)

    return True