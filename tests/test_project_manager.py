import tempfile
import unittest
from pathlib import Path

from src.project.project_manager import (
    create_project_workspace,
    validate_project_name,
)


class TestProjectManager(unittest.TestCase):

    def test_validate_project_name(self):

        result = validate_project_name(
            "Portfolio Website"
        )

        self.assertEqual(
            result,
            "Portfolio_Website"
        )

    def test_validate_project_name_empty(self):

        with self.assertRaises(ValueError):

            validate_project_name("")

    def test_validate_project_name_invalid(self):

        with self.assertRaises(ValueError):

            validate_project_name(
                "Project/Test"
            )

    def test_create_project_workspace(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            workspace = create_project_workspace(
                project_name="TestProject",
                base_path=temp_dir
            )

            self.assertEqual(
                workspace.project_name,
                "TestProject"
            )

            self.assertTrue(
                workspace.project_path.exists()
            )

            self.assertTrue(
                workspace.reports_path.exists()
            )

            self.assertEqual(
                workspace.reports_path,
                workspace.project_path / "reports"
            )


if __name__ == "__main__":
    unittest.main()