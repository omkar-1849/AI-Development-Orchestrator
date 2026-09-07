from src.automation.antigravity_automation import AntigravityAutomation


def test_antigravity_response():

    automation = AntigravityAutomation()

    result = automation.execute(
        "Reply with HI only. Do not explain anything."
    )

    print(result)


if __name__ == "__main__":
    test_antigravity_response()