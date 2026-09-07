import importlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_setup_module():
    """
    Load src/orchestrator/setup.py directly without triggering
    src/orchestrator/__init__.py (which imports phase_runner
    and its pyperclip/pyautogui dependencies).
    """
    spec = importlib.util.spec_from_file_location(
        "orchestrator_setup",
        Path(__file__).resolve().parent.parent
        / "src" / "orchestrator" / "setup.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup_module = _load_setup_module()
setup_orchestrator = setup_module.setup_orchestrator
OrchestratorSetup = setup_module.OrchestratorSetup


class TestProjectIntegration(unittest.TestCase):

    @patch.object(setup_module, "create_project_workspace")
    def test_setup_creates_workspace_when_path_is_none(self, mock_create):
        """
        When project_name is provided but project_path is None,
        setup_orchestrator should create a workspace dynamically
        and populate project_path from the generated workspace.
        """

        with tempfile.TemporaryDirectory() as temp_dir:

            mock_create.return_value = type(
                "ProjectWorkspace",
                (),
                {
                    "project_name": "MyWebsite",
                    "project_path": Path(temp_dir) / "MyWebsite",
                    "reports_path": Path(temp_dir) / "MyWebsite" / "reports",
                },
            )()

            setup = setup_orchestrator(
                project_name="MyWebsite",
                project_path=None,
                requirement_collector=lambda: "Build a website",
            )

        mock_create.assert_called_once_with("MyWebsite")
        self.assertEqual(setup.project_name, "MyWebsite")
        self.assertEqual(
            setup.project_path,
            str(Path(temp_dir) / "MyWebsite"),
        )
        self.assertIsInstance(setup, OrchestratorSetup)

    @patch.object(setup_module, "create_project_workspace")
    def test_setup_uses_explicit_path_when_provided(self, mock_create):
        """
        When both project_name and project_path are explicitly provided,
        the explicit path should be used without calling
        create_project_workspace.
        """

        setup = setup_orchestrator(
            project_name="ExplicitProject",
            project_path="C:/explicit/path",
            requirement_collector=lambda: "Test requirement",
        )

        mock_create.assert_not_called()
        self.assertEqual(setup.project_name, "ExplicitProject")
        self.assertEqual(setup.project_path, "C:/explicit/path")

    @patch.object(setup_module, "create_project_workspace")
    def test_setup_collects_project_name_when_none(self, mock_create):
        """
        When project_name is None and a project_name_collector
        is provided, the collector should be called to get the name.
        """

        with tempfile.TemporaryDirectory() as temp_dir:

            mock_create.return_value = type(
                "ProjectWorkspace",
                (),
                {
                    "project_name": "CollectedProject",
                    "project_path": Path(temp_dir) / "CollectedProject",
                    "reports_path": Path(temp_dir) / "CollectedProject" / "reports",
                },
            )()

            setup = setup_orchestrator(
                project_name=None,
                project_path=None,
                requirement_collector=lambda: "Build something",
                project_name_collector=lambda: "CollectedProject",
            )

        self.assertEqual(setup.project_name, "CollectedProject")
        mock_create.assert_called_once_with("CollectedProject")

    def test_setup_workspace_creates_reports_directory(self):
        """
        End-to-end: verify that create_project_workspace actually
        creates the reports directory on disk.
        """

        with tempfile.TemporaryDirectory() as temp_dir:

            from src.project.project_manager import (
                create_project_workspace,
            )

            workspace = create_project_workspace(
                project_name="E2EProject",
                base_path=temp_dir,
            )

            self.assertTrue(workspace.reports_path.exists())
            self.assertTrue(workspace.project_path.exists())

    def test_setup_phase_state_uses_dynamic_name(self):
        """
        Verify that the PhaseState created during setup uses the
        dynamically provided project name.
        """

        setup = setup_orchestrator(
            project_name="DynamicName",
            project_path="C:/some/path",
            requirement_collector=lambda: "Test requirement",
        )

        self.assertEqual(
            setup.phase_state.project_name,
            "DynamicName",
        )
        self.assertEqual(
            setup.phase_state.current_phase,
            1,
        )
        self.assertEqual(
            setup.phase_state.current_attempt,
            1,
        )

    @patch.object(setup_module, "create_project_workspace")
    def test_setup_normalized_name_from_workspace(self, mock_create):
        """
        Verify that when workspace is created, the project_name
        returned by setup matches the workspace's normalized name.
        """

        with tempfile.TemporaryDirectory() as temp_dir:

            mock_create.return_value = type(
                "ProjectWorkspace",
                (),
                {
                    "project_name": "My_App",
                    "project_path": Path(temp_dir) / "My_App",
                    "reports_path": Path(temp_dir) / "My_App" / "reports",
                },
            )()

            setup = setup_orchestrator(
                project_name="My App",
                project_path=None,
                requirement_collector=lambda: "Build an app",
            )

        # The name in setup should come from the workspace
        self.assertEqual(setup.project_name, "My_App")


if __name__ == "__main__":
    unittest.main()
