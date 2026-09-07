import unittest

from src.automation.mock_automation import MockAutomation
from src.automation.automation_result import AutomationResult


class TestMockAutomation(unittest.TestCase):

    def test_execute_returns_automation_result(self):
        automation = MockAutomation()
        result = automation.execute("Test prompt")
        self.assertIsInstance(result, AutomationResult)

    def test_execute_returns_success(self):
        automation = MockAutomation()
        result = automation.execute("Test prompt")
        self.assertTrue(result.success)

    def test_execute_has_output(self):
        automation = MockAutomation()
        result = automation.execute("Test prompt")
        self.assertIsNotNone(result.output)
        self.assertIn("Mock automation completed", result.output)

    def test_execute_has_no_error(self):
        automation = MockAutomation()
        result = automation.execute("Test prompt")
        self.assertIsNone(result.error)

    def test_result_success_attribute_works(self):
        """Verify .success attribute access works (previously raised AttributeError)."""
        automation = MockAutomation()
        result = automation.execute("Test prompt")
        # This should not raise AttributeError
        success_value = result.success
        self.assertIs(success_value, True)


if __name__ == "__main__":
    unittest.main()