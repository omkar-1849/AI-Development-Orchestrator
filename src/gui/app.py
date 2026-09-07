import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from src.gui.controller import OrchestratorController
from src.gui.dashboard_view import DashboardView
from src.gui.report_view import ReportDialog
from src.gui.setup_view import SetupView


class OrchestratorApp(tk.Tk):
    """
    Main application window for the AI Development Orchestrator Desktop GUI.
    Manages view transitions, event polling loop, and top-level theme settings.
    """

    def __init__(self):
        super().__init__()
        self.title("AI Development Orchestrator")
        self.geometry("980x720")
        self.minsize(800, 600)
        self.configure(bg="#1e1e2e")

        self.controller = OrchestratorController()

        self._configure_styles()
        self._center_window()
        self._create_views()

        # Start non-blocking polling timer for background events
        self.after(100, self._poll_events)

    def _configure_styles(self):
        """Configure ttk styles for dark modern palette."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Scrollbar styling
        style.configure(
            "Vertical.TScrollbar",
            background="#252538",
            troughcolor="#181825",
            bordercolor="#181825",
            arrowcolor="#a6adc8",
            relief="flat",
        )

    def _center_window(self):
        self.update_idletasks()
        w = 980
        h = 720
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _create_views(self):
        self.view_container = tk.Frame(self, bg="#1e1e2e")
        self.view_container.pack(fill=tk.BOTH, expand=True)

        # Screen 1: Project Setup View
        self.setup_view = SetupView(
            self.view_container,
            on_start_callback=self._on_start_project,
        )

        # Screen 2: Execution Dashboard View
        self.dashboard_view = DashboardView(
            self.view_container,
            on_view_report=self._on_view_report,
            on_open_folder=self._on_open_folder,
            on_new_project=self._on_new_project,
        )

        # Show initial screen
        self.show_setup_view()

    def show_setup_view(self):
        self.dashboard_view.pack_forget()
        self.setup_view.pack(fill=tk.BOTH, expand=True)

    def show_dashboard_view(self, project_name: str):
        self.setup_view.pack_forget()
        self.dashboard_view.init_dashboard(project_name)
        self.dashboard_view.pack(fill=tk.BOTH, expand=True)

    def _on_start_project(self, project_name: str, requirements: str):
        """Called when user clicks Start Project."""
        valid, err = self.controller.validate_inputs(project_name, requirements)
        if not valid:
            self.setup_view.show_error(err)
            self.setup_view.set_loading(False)
            return

        # Transition to dashboard view
        self.show_dashboard_view(project_name)

        # Start background orchestration
        try:
            self.controller.start_orchestration(project_name, requirements)
        except Exception as exc:
            messagebox.showerror(
                "Launch Error",
                f"Failed to start orchestrator process: {exc}",
                parent=self,
            )
            self.show_setup_view()
            self.setup_view.set_loading(False)

    def _poll_events(self):
        """
        Poll background thread events from the controller queue.
        Guaranteed to execute on Tkinter's main UI thread.
        """
        events = self.controller.get_pending_events()
        for event in events:
            self.dashboard_view.handle_event(event)

        # Reschedule next check in 100ms
        self.after(100, self._poll_events)

    def _on_view_report(self):
        """Open read-only dialog displaying final project report."""
        content = self.controller.get_final_report_content()
        path = self.controller.final_report_path
        ReportDialog(
            parent=self,
            report_content=content,
            report_path=path,
            title=f"Final Report - {self.controller.project_name or 'Project'}",
        )

    def _on_open_folder(self):
        """Safely open workspace directory in Windows Explorer."""
        success = self.controller.open_project_folder()
        if not success:
            path_str = self.controller.project_path or "Unknown path"
            messagebox.showwarning(
                "Workspace Not Found",
                f"Project directory is not accessible yet:\n{path_str}",
                parent=self,
            )

    def _on_new_project(self):
        """Reset state and return to Setup view."""
        self.controller.reset()
        self.setup_view.reset_view()
        self.show_setup_view()


def launch_app():
    """Entry point to start the AI Development Orchestrator GUI."""
    app = OrchestratorApp()
    app.mainloop()
