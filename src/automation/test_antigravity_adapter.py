from src.automation.mock_automation import MockAutomation
from src.implementer.antigravity_adapter import AntigravityAdapter


def test_antigravity_adapter():

    automation = MockAutomation()

    implementer = AntigravityAdapter(
        automation=automation
    )

    result = implementer.execute(
        "Create a Python project with a simple main.py file"
    )

    print(result)


if __name__ == "__main__":
    test_antigravity_adapter()