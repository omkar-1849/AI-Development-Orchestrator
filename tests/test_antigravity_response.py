import unittest
from unittest.mock import patch

from src.automation.antigravity_automation import AntigravityAutomation
from src.automation.automation_result import AutomationResult


class TestAntigravityResponse(unittest.TestCase):

    @patch.object(AntigravityAutomation, "execute")
    def test_execute_response_handling(self, mock_execute):
        mock_execute.return_value = AutomationResult(
            success=True,
            output="HI",
            error=None,
        )

        automation = AntigravityAutomation()
        result = automation.execute("Reply with HI only. Do not explain anything.")

        self.assertIsInstance(result, AutomationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "HI")
        self.assertIsNone(result.error)

    @patch.object(AntigravityAutomation, "execute")
    def test_execute_failure_handling(self, mock_execute):
        mock_execute.return_value = AutomationResult(
            success=False,
            output=None,
            error="Timeout waiting for Antigravity response",
        )

        automation = AntigravityAutomation()
        result = automation.execute("Reply with HI only.")

        self.assertFalse(result.success)
        self.assertIn("Timeout", result.error)


if __name__ == "__main__":
    unittest.main()