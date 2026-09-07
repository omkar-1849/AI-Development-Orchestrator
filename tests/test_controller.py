import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.gui.controller import OrchestratorController
from src.orchestrator.events import EventType, OrchestratorEvent


class TestOrchestratorController(unittest.TestCase):

    def setUp(self):
        self.controller = OrchestratorController()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validation(self):
        # Empty name
        valid, msg = self.controller.validate_inputs("", "Build an app")
        self.assertFalse(valid)
        self.assertIn("cannot be empty", msg)

        # Invalid characters
        valid, msg = self.controller.validate_inputs("My@App!", "Build an app")
        self.assertFalse(valid)

        # Empty requirements
        valid, msg = self.controller.validate_inputs("MyApp", "")
        self.assertFalse(valid)
        self.assertIn("requirements cannot be empty", msg.lower())

        # Valid inputs
        valid, msg = self.controller.validate_inputs("MyApp", "Build an app")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_event_queueing_and_retrieval(self):
        # Push events via internal handler
        event1 = OrchestratorEvent(
            event_type=EventType.PROJECT_SETUP_STARTED,
            message="Setup started",
        )
        event2 = OrchestratorEvent(
            event_type=EventType.PROJECT_WORKSPACE_CREATED,
            message="Workspace ready",
            data={"project_path": self.temp_dir},
        )

        self.controller._on_orchestrator_event(event1)
        self.controller._on_orchestrator_event(event2)

        self.assertEqual(self.controller.project_path, self.temp_dir)

        # Retrieve events
        events = self.controller.get_pending_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, EventType.PROJECT_SETUP_STARTED)
        self.assertEqual(events[1].event_type, EventType.PROJECT_WORKSPACE_CREATED)

        # Queue should now be empty
        self.assertEqual(len(self.controller.get_pending_events()), 0)

    def test_reset(self):
        self.controller.project_name = "OldProject"
        self.controller.project_path = "/old/path"
        self.controller.is_running = True
        self.controller.final_status = "COMPLETED"

        self.controller.reset()

        self.assertEqual(self.controller.project_name, "")
        self.assertIsNone(self.controller.project_path)
        self.assertFalse(self.controller.is_running)
        self.assertEqual(self.controller.final_status, "IDLE")

    def test_final_report_reading(self):
        self.controller.project_path = self.temp_dir
        report_file = os.path.join(self.temp_dir, "final_project_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Sample Report Content")

        content = self.controller.get_final_report_content()
        self.assertEqual(content, "# Sample Report Content")


if __name__ == "__main__":
    unittest.main()
