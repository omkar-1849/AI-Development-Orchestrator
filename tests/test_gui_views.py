import tkinter as tk
import unittest

from src.gui.dashboard_view import DashboardView
from src.gui.report_view import ReportDialog
from src.gui.setup_view import SetupView
from src.orchestrator.events import EventType, OrchestratorEvent


class TestGUIViews(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()  # Headless / hidden window

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_setup_view_creation_and_validation(self):
        started_args = []

        def on_start(name, reqs):
            started_args.append((name, reqs))

        view = SetupView(self.root, on_start_callback=on_start)

        # Initial state has placeholder active
        self.assertEqual(view.get_requirements(), "")

        # Set valid inputs
        view.name_entry.insert(0, "TestApp")
        view.req_text.delete("1.0", tk.END)
        view.req_text.insert("1.0", "Build a web app")
        view._placeholder_active = False

        self.assertEqual(view.get_project_name(), "TestApp")
        self.assertEqual(view.get_requirements(), "Build a web app")

        # Trigger start click
        view._on_start_clicked()
        self.assertEqual(len(started_args), 1)
        self.assertEqual(started_args[0], ("TestApp", "Build a web app"))

        # Test reset
        view.reset_view()
        self.assertEqual(view.get_project_name(), "")
        self.assertTrue(view._placeholder_active)
        view.destroy()

    def test_dashboard_view_events_and_stages(self):
        view = DashboardView(
            self.root,
            on_view_report=lambda: None,
            on_open_folder=lambda: None,
            on_new_project=lambda: None,
        )

        view.init_dashboard("DashboardTest")
        self.assertIn("DashboardTest", view.project_name_lbl.cget("text"))

        # Send SETUP event
        evt_setup = OrchestratorEvent(
            event_type=EventType.PROJECT_WORKSPACE_CREATED,
            message="Workspace created",
            level="SUCCESS",
            data={"project_path": "C:/fake/path"},
        )
        view.handle_event(evt_setup)
        self.assertEqual(view.stage_widgets["SETUP"]["status"].cget("text"), "Completed")
        self.assertIn("C:/fake/path", view.workspace_lbl.cget("text"))

        # Send PLANNER event
        evt_planner = OrchestratorEvent(
            event_type=EventType.PLANNER_STARTED,
            message="Planner analyzing",
            phase=1,
            attempt=1,
        )
        view.handle_event(evt_planner)
        self.assertEqual(view.stage_widgets["PLANNER"]["status"].cget("text"), "Running")
        self.assertEqual(view.activity_lbl.cget("text"), "Planner analyzing")

        # Send COMPLETE event
        evt_complete = OrchestratorEvent(
            event_type=EventType.PROJECT_COMPLETED,
            message="Completed successfully",
            level="SUCCESS",
        )
        view.handle_event(evt_complete)
        self.assertEqual(view.status_badge.cget("text"), "COMPLETED")
        self.assertTrue(view.bottom_bar.winfo_manager() != "")

        view.destroy()

    def test_report_dialog_creation(self):
        dialog = ReportDialog(
            parent=self.root,
            report_content="# Sample Report",
            report_path="C:/path/report.md",
        )
        self.assertIn("Sample Report", dialog.text_area.get("1.0", tk.END))
        dialog.destroy()


if __name__ == "__main__":
    unittest.main()
