import json
import unittest

from src.planner.planner_validator import validate_planner_response


class TestPlannerValidator(unittest.TestCase):

    def test_valid_response(self):
        valid_response = json.dumps({
            "task_id": "TASK-001",
            "status": "READY",
            "objective": "Test objective",
            "instructions": ["Do something"],
            "files_allowed": ["src/test.py"],
            "acceptance_criteria": ["It works"],
        })
        task = validate_planner_response(valid_response)
        self.assertEqual(task.task_id, "TASK-001")
        self.assertEqual(task.status, "READY")
        self.assertEqual(task.objective, "Test objective")
        self.assertEqual(task.instructions, ["Do something"])
        self.assertEqual(task.files_allowed, ["src/test.py"])
        self.assertEqual(task.acceptance_criteria, ["It works"])

    def test_markdown_fenced_response(self):
        fenced_response = """```json
{
    "task_id": "TASK-002",
    "status": "READY",
    "objective": "Build API",
    "instructions": ["Create app"],
    "files_allowed": ["app.py"],
    "acceptance_criteria": ["App runs"]
}
```"""
        task = validate_planner_response(fenced_response)
        self.assertEqual(task.task_id, "TASK-002")

    def test_conversational_wrapped_response(self):
        wrapped_response = """Here is your planned task:

{
    "task_id": "TASK-003",
    "status": "READY",
    "objective": "Build API",
    "instructions": ["Create app"],
    "files_allowed": ["app.py"],
    "acceptance_criteria": ["App runs"]
}

Let me know if you want changes."""
        task = validate_planner_response(wrapped_response)
        self.assertEqual(task.task_id, "TASK-003")

    def test_invalid_json_raises(self):
        invalid_json = '{"task_id": "TASK-004", "status": "READY"'
        with self.assertRaises(ValueError):
            validate_planner_response(invalid_json)

    def test_missing_fields_raises(self):
        missing_fields = json.dumps({
            "task_id": "TASK-005",
            "status": "READY",
            "objective": "Incomplete task",
        })
        with self.assertRaises(ValueError):
            validate_planner_response(missing_fields)

    def test_wrong_type_raises(self):
        wrong_type = json.dumps({
            "task_id": "TASK-006",
            "status": "READY",
            "objective": "Wrong type test",
            "instructions": "This should be a list",
            "files_allowed": [],
            "acceptance_criteria": [],
        })
        with self.assertRaises(ValueError):
            validate_planner_response(wrong_type)


if __name__ == "__main__":
    unittest.main()