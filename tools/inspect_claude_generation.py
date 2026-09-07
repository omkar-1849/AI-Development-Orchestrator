import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pywinauto import Desktop


def find_claude():
    desktop = Desktop(backend="uia")

    claude = desktop.window(title="Claude")

    if not claude.exists(timeout=5):
        raise RuntimeError("Claude window not found")

    return claude


def inspect_controls(claude):
    print("\n--- CLAUDE INTERACTIVE CONTROLS ---\n")

    for i, element in enumerate(claude.descendants()):
        try:
            info = element.element_info

            if info.control_type in ["Button", "Edit"]:
                print(f"[{i}]")
                print(f"Name: {info.name!r}")
                print(f"Type: {info.control_type}")
                print(f"Automation ID: {info.automation_id!r}")
                print(f"Class: {info.class_name!r}")
                print()

        except Exception:
            continue


def main():
    claude = find_claude()

    print("Claude found.")
    print()
    print("IMPORTANT:")
    print("Send a prompt to Claude manually NOW.")
    print("While Claude is actively generating, return here.")
    print()
    input("Press ENTER while Claude is generating...")

    time.sleep(1)

    inspect_controls(claude)


if __name__ == "__main__":
    main()
