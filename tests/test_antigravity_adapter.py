import unittest
from unittest.mock import MagicMock

from src.automation.mock_automation import MockAutomation
from src.automation.automation_result import AutomationResult
from src.implementer.antigravity_adapter import AntigravityAdapter
from src.implementer.implementer_result import ImplementerResult


class TestAntigravityAdapter(unittest.TestCase):

    def test_adapter_with_mock_automation(self):
        automation = MockAutomation()
        implementer = AntigravityAdapter(automation=automation)

        result = implementer.execute(
            "Create a Python project with a simple main.py file"
        )

        self.assertIsInstance(result, ImplementerResult)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Prompt sent to Antigravity successfully")
        self.assertIn("Mock automation completed", result.output)
        self.assertIsNone(result.error)

    def test_adapter_with_failing_automation(self):
        automation = MagicMock()
        automation.execute.return_value = AutomationResult(
            success=False,
            output=None,
            error="Connection to Antigravity timed out",
        )
        implementer = AntigravityAdapter(automation=automation)

        result = implementer.execute("Some prompt")

        self.assertIsInstance(result, ImplementerResult)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Antigravity execution failed")
        self.assertEqual(result.error, "Connection to Antigravity timed out")

    def test_adapter_handles_exceptions_gracefully(self):
        automation = MagicMock()
        automation.execute.side_effect = RuntimeError("Process crashed")
        implementer = AntigravityAdapter(automation=automation)

        result = implementer.execute("Some prompt")

        self.assertIsInstance(result, ImplementerResult)
        self.assertFalse(result.success)
        self.assertIn("Process crashed", result.error)


if __name__ == "__main__":
    unittest.main()
