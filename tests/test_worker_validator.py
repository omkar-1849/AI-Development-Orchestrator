import unittest

from src.worker.worker_validator import (
    validate_worker_response,
    WorkerValidationError,
)


class TestLegacyWorkerValidator(unittest.TestCase):

    def test_valid_response(self):
        response = """
{
    "implementation_summary": "Calculator module implemented successfully",
    "files_modified": [
        "calculator.py",
        "test_calculator.py"
    ],
    "changes_made": [
        "Added arithmetic functions",
        "Added division by zero handling"
    ],
    "acceptance_check": [
        "Addition works",
        "Subtraction works",
        "Division by zero handled"
    ],
    "blockers": "NONE"
}
"""
        result = validate_worker_response(response)
        self.assertEqual(result.implementation_summary, "Calculator module implemented successfully")
        self.assertEqual(result.files_modified, ["calculator.py", "test_calculator.py"])
        self.assertEqual(result.blockers, "NONE")

    def test_invalid_json_raises(self):
        response = """
{
    "implementation_summary": "Test"
    "files_modified": []
}
"""
        with self.assertRaises(WorkerValidationError):
            validate_worker_response(response)

    def test_missing_fields_raises(self):
        response = """
{
    "implementation_summary": "Test",
    "files_modified": []
}
"""
        with self.assertRaises(WorkerValidationError):
            validate_worker_response(response)

    def test_wrong_type_raises(self):
        response = """
{
    "implementation_summary": "Test",
    "files_modified": "calculator.py",
    "changes_made": [],
    "acceptance_check": [],
    "blockers": "NONE"
}
"""
        with self.assertRaises(WorkerValidationError):
            validate_worker_response(response)


if __name__ == "__main__":
    unittest.main()