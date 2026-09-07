from src.automation.antigravity_automation import AntigravityAutomation


def test_antigravity_automation():
    automation = AntigravityAutomation()

    result = automation.execute(
        "TEST PROMPT FROM ORCHESTRATOR"
    )

    print(result)


if __name__ == "__main__":
    test_antigravity_automation()