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

    def test_get_default_workspace_base_dir_with_desktop(self):
        from unittest.mock import patch, MagicMock
        from src.project.project_manager import get_default_workspace_base_dir

        fake_home = Path("C:/Users/JaneDoe")
        with patch("pathlib.Path.home", return_value=fake_home), \
             patch.object(Path, "exists", autospec=True) as mock_exists:
            # When checking if desktop exists
            mock_exists.side_effect = lambda p: p == fake_home / "Desktop"
            base_dir = get_default_workspace_base_dir()
            self.assertEqual(base_dir, fake_home / "Desktop" / "AIProjects")
            self.assertNotIn("omkar", str(base_dir).lower())
            self.assertIn("janedoe", str(base_dir).lower())

    def test_get_default_workspace_base_dir_fallback_without_desktop(self):
        from unittest.mock import patch
        from src.project.project_manager import get_default_workspace_base_dir

        fake_home = Path("C:/Users/JohnSmith")
        with patch("pathlib.Path.home", return_value=fake_home), \
             patch.object(Path, "exists", return_value=False):
            base_dir = get_default_workspace_base_dir()
            self.assertEqual(base_dir, fake_home / "AIProjects")
            self.assertNotIn("omkar", str(base_dir).lower())
            self.assertIn("johnsmith", str(base_dir).lower())

    def test_create_project_workspace_default_path_dynamic(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir) / "CustomUserHome"
            fake_desktop = fake_home / "Desktop"
            fake_desktop.mkdir(parents=True)

            with patch("pathlib.Path.home", return_value=fake_home):
                workspace = create_project_workspace(project_name="PortabilityProject")
                self.assertTrue(workspace.project_path.exists())
                self.assertTrue(workspace.reports_path.exists())
                self.assertEqual(
                    workspace.project_path,
                    fake_desktop / "AIProjects" / "PortabilityProject"
                )
                self.assertIn("customuserhome", str(workspace.project_path).lower())

    def test_no_hardcoded_user_paths_in_src(self):
        """Verify that no source file in src/ contains hardcoded 'omkar'."""
        src_dir = Path(__file__).resolve().parent.parent / "src"
        violations = []
        for py_file in src_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            if "omkar" in text.lower():
                violations.append(str(py_file))
        self.assertEqual(violations, [], f"Hardcoded 'omkar' found in: {violations}")


if __name__ == "__main__":
    unittest.main()