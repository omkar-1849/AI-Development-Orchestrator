import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.automation.antigravity_automation import AntigravityAutomation
from src.automation.automation_result import AutomationResult


class TestAntigravityAutomation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.temp_dir, "test_cache.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.automation.antigravity_automation.CACHE_PATH")
    def test_load_cached_exe_name(self, mock_cache_path):
        mock_cache_path.__fspath__ = lambda self: self.cache_path
        with patch("src.automation.antigravity_automation.CACHE_PATH", self.cache_path):
            with open(self.cache_path, "w") as f:
                json.dump({"exe_name": "TestAntigravity.exe"}, f)

            automation = AntigravityAutomation()
            self.assertEqual(automation._cached_exe_name, "TestAntigravity.exe")

    def test_automation_result_contract(self):
        result = AutomationResult(success=True, output="Done", error=None)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Done")
        self.assertIsNone(result.error)

    @patch.object(AntigravityAutomation, "execute")
    def test_mocked_execution(self, mock_execute):
        mock_execute.return_value = AutomationResult(
            success=True,
            output="Mocked antigravity output",
        )
        automation = AntigravityAutomation()
        result = automation.execute("TEST PROMPT")
        self.assertTrue(result.success)
        self.assertIn("Mocked", result.output)


if __name__ == "__main__":
    unittest.main()