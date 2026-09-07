from io import StringIO
import unittest

from src.input.requirement_collector import (
    BANNER_TEXT,
    collect_requirements,
    get_project_requirements,
    normalize_requirements,
)
from src.planner.planner_prompt import build_planner_prompt


class TestRequirementCollector(unittest.TestCase):

    def test_normalize_requirements_basic(self):
        raw = "   \n  I want a REST API   \n  with JWT authentication.  \n\n  "
        expected = "I want a REST API\n  with JWT authentication."
        self.assertEqual(normalize_requirements(raw), expected)

    def test_normalize_requirements_collapses_excessive_blank_lines(self):
        raw = "Line 1\n\n\n\n\nLine 2\n\n\nLine 3"
        expected = "Line 1\n\nLine 2\n\nLine 3"
        self.assertEqual(normalize_requirements(raw), expected)

    def test_normalize_requirements_empty(self):
        self.assertEqual(normalize_requirements(""), "")
        self.assertEqual(normalize_requirements("   \n\n \t  "), "")

    def test_normalize_requirements_windows_crlf(self):
        raw = "Line 1\r\nLine 2\r\n\r\n\r\n\r\nLine 3\r\n"
        expected = "Line 1\nLine 2\n\nLine 3"
        self.assertEqual(normalize_requirements(raw), expected)

    def test_collect_requirements_multiline(self):
        inputs = iter([
            "I want to build a Python REST API",
            "with JWT authentication and MySQL.",
            "END"
        ])
        output_buffer = []

        result = collect_requirements(
            input_func=lambda: next(inputs),
            output_func=output_buffer.append
        )

        expected = (
            "I want to build a Python REST API\n"
            "with JWT authentication and MySQL."
        )
        self.assertEqual(result, expected)

    def test_collect_requirements_case_insensitive_terminator(self):
        inputs = iter([
            "Create a calculator module",
            "end"
        ])
        output_buffer = []

        result = collect_requirements(
            input_func=lambda: next(inputs),
            output_func=output_buffer.append
        )

        self.assertEqual(result, "Create a calculator module")

    def test_collect_requirements_rejects_empty_and_retries(self):
        # First attempt: immediately type END (empty)
        # Second attempt: only spaces then END (empty)
        # Third attempt: valid requirements then END
        inputs = iter([
            "END",
            "   ",
            "   \t  ",
            "END",
            "Build an authentication service",
            "- Support OAuth2",
            "- Support bcrypt password hashing",
            "END"
        ])
        output_buffer = []

        result = collect_requirements(
            input_func=lambda: next(inputs),
            output_func=output_buffer.append
        )

        expected = (
            "Build an authentication service\n"
            "- Support OAuth2\n"
            "- Support bcrypt password hashing"
        )
        self.assertEqual(result, expected)

        # Verify error message was displayed for empty attempts
        error_messages = [msg for msg in output_buffer if "[ERROR]" in msg]
        self.assertEqual(len(error_messages), 2)

    def test_get_project_requirements_cli(self):
        inputs = iter([
            "Task from CLI",
            "END"
        ])
        result = get_project_requirements(
            source="cli",
            input_func=lambda: next(inputs),
            output_func=lambda _: None
        )
        self.assertEqual(result, "Task from CLI")

    def test_get_project_requirements_invalid_source(self):
        with self.assertRaises(ValueError):
            get_project_requirements(source="unknown")

    def test_collected_requirements_integration_with_planner_prompt(self):
        inputs = iter([
            "Create a Python calculator module that supports:",
            "- Addition",
            "- Subtraction",
            "Include proper error handling for division by zero.",
            "END"
        ])
        user_request = collect_requirements(
            input_func=lambda: next(inputs),
            output_func=lambda _: None
        )

        prompt = build_planner_prompt(user_request)
        self.assertIn("USER REQUEST:", prompt)
        self.assertIn("Create a Python calculator module that supports:", prompt)
        self.assertIn("- Addition", prompt)
        self.assertIn("- Subtraction", prompt)
        self.assertIn("Include proper error handling for division by zero.", prompt)


if __name__ == "__main__":
    unittest.main()
