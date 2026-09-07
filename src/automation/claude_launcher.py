from typing import Optional

from pywinauto import Desktop

from src.automation.application_discovery import (
    CLAUDE_TARGET,
    ApplicationDiscovery,
    ApplicationDiscoveryError,
    ensure_desktop_access,
)


def find_claude(timeout: float = 10.0):
    """
    Locate, launch (if absent), restore, activate, and focus the Claude Desktop window.
    Uses ApplicationDiscovery for robust multi-strategy discovery and launch lifecycle.
    Returns pywinauto WindowSpecification or None if unavailable.
    """
    ensure_desktop_access()
    print("Searching for Claude window...")

    discovery = ApplicationDiscovery(
        discovery_timeout=timeout / 2.0,
        startup_timeout=timeout,
    )

    try:
        hwnd, title, exe_name = discovery.ensure_application_ready(
            CLAUDE_TARGET, timeout=timeout
        )
        print(f"Claude window ready: '{title}' ({exe_name}) [HWND: {hwnd}]")

        desktop = Desktop(backend="uia")
        claude = desktop.window(handle=hwnd)
        try:
            claude.set_focus()
        except Exception:
            pass
        return claude

    except ApplicationDiscoveryError as disc_err:
        print(f"FAILED: Claude lifecycle error: {disc_err}")
        return None
    except Exception as exc:
        print(f"FAILED: Unexpected error locating Claude window: {exc}")
        return None