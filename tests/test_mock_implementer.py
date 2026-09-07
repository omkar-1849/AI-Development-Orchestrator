import unittest

from src.implementer.mock_implementer import MockImplementer
from src.implementer.implementer_result import ImplementerResult


class TestMockImplementer(unittest.TestCase):

    def test_execute_returns_implementer_result(self):
        implementer = MockImplementer()
        result = implementer.execute("Create a test function")
        self.assertIsInstance(result, ImplementerResult)

    def test_execute_returns_success(self):
        implementer = MockImplementer()
        result = implementer.execute("Create a test function")
        self.assertTrue(result.success)

    def test_execute_has_message(self):
        implementer = MockImplementer()
        result = implementer.execute("Create a test function")
        self.assertIn("Mock implementation completed", result.message)

    def test_execute_has_output_with_task(self):
        implementer = MockImplementer()
        result = implementer.execute("Create a test function")
        self.assertIn("Create a test function", result.output)

    def test_execute_has_no_error(self):
        implementer = MockImplementer()
        result = implementer.execute("Create a test function")
        self.assertIsNone(result.error)


if __name__ == "__main__":
    unittest.main()