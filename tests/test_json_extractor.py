import unittest
from src.utils.json_extractor import extract_json_object, JsonExtractionError

class TestJsonExtractor(unittest.TestCase):
    def test_pure_json_object(self):
        text = '{"key": "value"}'
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_json_surrounding_whitespace(self):
        text = '   \n \t {"key": "value"} \n  '
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_markdown_json_fenced(self):
        text = '```json\n{"key": "value"}\n```'
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_markdown_generic_fenced(self):
        text = '```\n{"key": "value"}\n```'
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_conversational_text_before(self):
        text = 'Here is the JSON:\n{"key": "value"}'
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_conversational_text_after(self):
        text = '{"key": "value"}\nThis is the JSON you asked for.'
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_conversational_both(self):
        text = 'Here is the data:\n{"key": "value"}\nHope this helps!'
        self.assertEqual(extract_json_object(text), {"key": "value"})

    def test_nested_json_objects(self):
        text = '{"outer": {"inner": "value"}}'
        self.assertEqual(extract_json_object(text), {"outer": {"inner": "value"}})

    def test_nested_arrays(self):
        text = '{"list": [{"item": 1}, {"item": 2}]}'
        self.assertEqual(extract_json_object(text), {"list": [{"item": 1}, {"item": 2}]})

    def test_braces_inside_strings(self):
        text = '{"code": "if (x) { y; }"}'
        self.assertEqual(extract_json_object(text), {"code": "if (x) { y; }"})

    def test_escaped_quotes_inside_strings(self):
        text = '{"message": "He said \\"Hello\\""}'
        self.assertEqual(extract_json_object(text), {"message": 'He said "Hello"'})

    def test_invalid_json_raises(self):
        text = '{"key": "value"'
        with self.assertRaises(JsonExtractionError):
            extract_json_object(text)

    def test_empty_string_raises(self):
        with self.assertRaises(JsonExtractionError):
            extract_json_object("")
        with self.assertRaises(JsonExtractionError):
            extract_json_object("   ")

    def test_text_no_json_raises(self):
        text = 'There is no JSON here, just { some braces } that are not valid JSON.'
        with self.assertRaises(JsonExtractionError):
            extract_json_object(text)

    def test_multiple_json_objects(self):
        text = 'First object:\n{"id": 1}\nSecond object:\n{"id": 2}'
        self.assertEqual(extract_json_object(text), {"id": 1})

    def test_literal_newline_inside_json_string(self):
        # Construct raw JSON text with an actual literal newline character (ASCII 10)
        # inside the string value, not an already-escaped \n sequence.
        text = '{"objective": "Line one\nLine two"}'
        result = extract_json_object(text)
        self.assertEqual(result, {"objective": "Line one\nLine two"})

    def test_literal_tab_inside_json_string(self):
        # Construct raw JSON text with an actual literal tab character (ASCII 9)
        text = '{"objective": "Col1\tCol2"}'
        result = extract_json_object(text)
        self.assertEqual(result, {"objective": "Col1\tCol2"})

    def test_literal_carriage_return_inside_json_string(self):
        # Construct raw JSON text with an actual literal carriage return character (ASCII 13)
        text = '{"objective": "Line1\rLine2"}'
        result = extract_json_object(text)
        self.assertEqual(result, {"objective": "Line1\rLine2"})

    def test_control_character_combined_with_braces_inside_string(self):
        text = '{"code": "function run() {\n\tconst data = { ready: true };\n\treturn data;\n}"}'
        result = extract_json_object(text)
        self.assertEqual(
            result,
            {"code": "function run() {\n\tconst data = { ready: true };\n\treturn data;\n}"}
        )

    def test_existing_valid_escaped_sequences_remain_correct(self):
        # Raw text contains valid JSON escape sequences (\n, \t)
        text = r'{"objective": "Line one\nLine two", "tab": "A\tB"}'
        result = extract_json_object(text)
        self.assertEqual(result, {"objective": "Line one\nLine two", "tab": "A\tB"})

    def test_malformed_json_structural_errors_still_fail(self):
        # Unquoted values must still fail
        text_unquoted = '{"task_id": "TASK-004", "status": READY}'
        with self.assertRaises(JsonExtractionError):
            extract_json_object(text_unquoted)

        # Missing comma must still fail
        text_missing_comma = '{"task_id": "TASK-001" "status": "READY"}'
        with self.assertRaises(JsonExtractionError):
            extract_json_object(text_missing_comma)

        # Unclosed quote must still fail
        text_unclosed_quote = '{"task_id": "TASK-001, "status": "READY"}'
        with self.assertRaises(JsonExtractionError):
            extract_json_object(text_unclosed_quote)

    def test_markdown_fenced_with_literal_control_characters(self):
        text = "```json\n" + '{"objective": "Line one\nLine two\tTabbed"}' + "\n```"
        result = extract_json_object(text)
        self.assertEqual(result, {"objective": "Line one\nLine two\tTabbed"})

    def test_real_planner_response_regression(self):
        # Realistic production failure pattern: Planner response with literal newline inside string
        response_text = (
            "Here is the plan for the initial phase:\n\n"
            "{\n"
            '  "task_id": "TASK-001",\n'
            '  "status": "READY",\n'
            '  "objective": "Build a Python-based command-line Task Management application.\n'
            'The CLI should support adding, listing, and completing tasks.",\n'
            '  "instructions": [\n'
            '    "Initialize src/tasks.py with Task dataclass",\n'
            '    "Create main CLI entry point in src/main.py\nwith argparse support",\n'
            '    "Write tests in tests/test_tasks.py"\n'
            "  ],\n"
            '  "files_allowed": [\n'
            '    "src/tasks.py",\n'
            '    "src/main.py",\n'
            '    "tests/test_tasks.py"\n'
            "  ],\n"
            '  "acceptance_criteria": [\n'
            '    "CLI command add creates tasks",\n'
            '    "CLI command list displays tasks",\n'
            '    "Unit tests pass with 100% success"\n'
            "  ]\n"
            "}\n\n"
            "Please review and proceed."
        )
        result = extract_json_object(response_text)
        self.assertEqual(result["task_id"], "TASK-001")
        self.assertEqual(result["status"], "READY")
        self.assertEqual(
            result["objective"],
            "Build a Python-based command-line Task Management application.\n"
            "The CLI should support adding, listing, and completing tasks."
        )
        self.assertEqual(len(result["instructions"]), 3)
        self.assertEqual(
            result["instructions"][1],
            "Create main CLI entry point in src/main.py\nwith argparse support"
        )
        self.assertEqual(
            result["files_allowed"],
            ["src/tasks.py", "src/main.py", "tests/test_tasks.py"]
        )
        self.assertEqual(len(result["acceptance_criteria"]), 3)
        self.assertEqual(result["acceptance_criteria"][0], "CLI command add creates tasks")

if __name__ == '__main__':
    unittest.main()
