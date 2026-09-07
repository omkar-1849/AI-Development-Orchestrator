from src.automation.mock_automation import MockAutomation


def test_mock_automation():
    automation = MockAutomation()

    result = automation.execute(
        "Create a test project and add a README file."
    )

    print(result)


if __name__ == "__main__":
    test_mock_automation()