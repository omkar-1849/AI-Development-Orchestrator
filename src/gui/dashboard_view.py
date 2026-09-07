import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Callable, Dict, Optional

from src.orchestrator.events import EventType, OrchestratorEvent


class DashboardView(tk.Frame):
    """
    Screen 2: Project Execution Dashboard.
    Displays live pipeline stage progress, current activity, phase/attempt metrics,
    scrollable color-coded activity log, and completion actions.
    """

    STAGES = [
        ("SETUP", "Project Setup"),
        ("PLANNER", "Planner"),
        ("WORKER", "Worker"),
        ("IMPLEMENTATION", "Implementation"),
        ("REPORT", "Report Detection"),
        ("REVIEWER", "Reviewer"),
        ("DECISION", "Decision Engine"),
        ("HANDOFF", "Final Handoff"),
    ]

    # Stage mappings from EventType
    EVENT_STAGE_MAP = {
        EventType.PROJECT_SETUP_STARTED: ("SETUP", "RUNNING"),
        EventType.PROJECT_WORKSPACE_CREATED: ("SETUP", "COMPLETED"),
        EventType.REQUIREMENTS_RECEIVED: ("SETUP", "COMPLETED"),
        EventType.PLANNER_STARTED: ("PLANNER", "RUNNING"),
        EventType.PLANNER_RESPONSE_RECEIVED: ("PLANNER", "RUNNING"),
        EventType.PLANNER_VALIDATED: ("PLANNER", "COMPLETED"),
        EventType.WORKER_STARTED: ("WORKER", "RUNNING"),
        EventType.TASK_DISPATCHED: ("WORKER", "COMPLETED"),
        EventType.IMPLEMENTATION_STARTED: ("IMPLEMENTATION", "RUNNING"),
        EventType.IMPLEMENTATION_COMPLETED: ("IMPLEMENTATION", "COMPLETED"),
        EventType.REPORT_WAITING: ("REPORT", "RUNNING"),
        EventType.REPORT_RECEIVED: ("REPORT", "COMPLETED"),
        EventType.REVIEW_STARTED: ("REVIEWER", "RUNNING"),
        EventType.REVIEW_RESPONSE_RECEIVED: ("REVIEWER", "RUNNING"),
        EventType.REVIEW_APPROVED: ("REVIEWER", "COMPLETED"),
        EventType.REVIEW_REJECTED: ("REVIEWER", "COMPLETED"),
        EventType.NEXT_PHASE: ("DECISION", "COMPLETED"),
        EventType.RETRY_PHASE: ("DECISION", "RUNNING"),
        EventType.HANDOFF_STARTED: ("HANDOFF", "RUNNING"),
        EventType.HANDOFF_PREPARING: ("HANDOFF", "RUNNING"),
        EventType.HANDOFF_COMPLETED: ("HANDOFF", "COMPLETED"),
        EventType.PROJECT_COMPLETED: ("DECISION", "COMPLETED"),
        EventType.PROJECT_BLOCKED: ("DECISION", "FAILED"),
        EventType.PROJECT_FAILED: ("DECISION", "FAILED"),
    }

    def __init__(
        self,
        parent: tk.Widget,
        on_view_report: Callable[[], None],
        on_open_folder: Callable[[], None],
        on_new_project: Callable[[], None],
        **kwargs,
    ):
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self.on_view_report = on_view_report
        self.on_open_folder = on_open_folder
        self.on_new_project = on_new_project

        self.stage_widgets: Dict[str, Dict[str, tk.Widget]] = {}
        self.phase_count: int = 1
        self.attempt_count: int = 1
        self.retry_count: int = 0

        self._create_widgets()

    def _create_widgets(self):
        container = tk.Frame(self, bg="#1e1e2e", padx=24, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # ----------------- Top Header Bar -----------------
        header_frame = tk.Frame(container, bg="#252538", padx=16, pady=12)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        header_left = tk.Frame(header_frame, bg="#252538")
        header_left.pack(side=tk.LEFT, fill=tk.Y)

        self.project_name_lbl = tk.Label(
            header_left,
            text="Project: Initializing...",
            font=("Segoe UI", 13, "bold"),
            fg="#f8f8f2",
            bg="#252538",
        )
        self.project_name_lbl.pack(anchor="w")

        self.workspace_lbl = tk.Label(
            header_left,
            text="Workspace: Resolving path...",
            font=("Segoe UI", 9),
            fg="#a6adc8",
            bg="#252538",
        )
        self.workspace_lbl.pack(anchor="w", pady=(2, 0))

        # Status badge on right
        self.status_badge = tk.Label(
            header_frame,
            text="RUNNING",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#3b82f6",
            padx=12,
            pady=4,
        )
        self.status_badge.pack(side=tk.RIGHT)

        # ----------------- Middle Split Layout -----------------
        content_split = tk.Frame(container, bg="#1e1e2e")
        content_split.pack(fill=tk.BOTH, expand=True)

        # Left Column: Pipeline Progress & Phase Info
        left_col = tk.Frame(content_split, bg="#1e1e2e", width=290)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_col.pack_propagate(False)

        # Pipeline Stages Card
        stages_card = tk.Frame(left_col, bg="#252538", padx=14, pady=12)
        stages_card.pack(fill=tk.X, pady=(0, 12))

        stages_title = tk.Label(
            stages_card,
            text="PIPELINE PROGRESS",
            font=("Segoe UI", 10, "bold"),
            fg="#818cf8",
            bg="#252538",
        )
        stages_title.pack(anchor="w", pady=(0, 10))

        # Add stage rows
        for stage_id, stage_name in self.STAGES:
            row = tk.Frame(stages_card, bg="#252538")
            row.pack(fill=tk.X, pady=3)

            icon = tk.Label(
                row,
                text="○",
                font=("Segoe UI", 11, "bold"),
                fg="#6c7086",
                bg="#252538",
                width=2,
            )
            icon.pack(side=tk.LEFT)

            name = tk.Label(
                row,
                text=stage_name,
                font=("Segoe UI", 9),
                fg="#cdd6f4",
                bg="#252538",
            )
            name.pack(side=tk.LEFT, padx=(4, 0))

            status = tk.Label(
                row,
                text="Pending",
                font=("Segoe UI", 8),
                fg="#6c7086",
                bg="#252538",
            )
            status.pack(side=tk.RIGHT)

            self.stage_widgets[stage_id] = {
                "icon": icon,
                "name": name,
                "status": status,
            }

        # Current Phase Metrics Card
        phase_card = tk.Frame(left_col, bg="#252538", padx=14, pady=12)
        phase_card.pack(fill=tk.X)

        phase_title = tk.Label(
            phase_card,
            text="CURRENT PHASE & ATTEMPT",
            font=("Segoe UI", 10, "bold"),
            fg="#818cf8",
            bg="#252538",
        )
        phase_title.pack(anchor="w", pady=(0, 8))

        metrics_grid = tk.Frame(phase_card, bg="#252538")
        metrics_grid.pack(fill=tk.X)

        # Phase Counter
        m1 = tk.Frame(metrics_grid, bg="#181825", padx=8, pady=6)
        m1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        tk.Label(m1, text="Phase", font=("Segoe UI", 8), fg="#a6adc8", bg="#181825").pack()
        self.phase_val_lbl = tk.Label(m1, text="1", font=("Segoe UI", 13, "bold"), fg="#f8f8f2", bg="#181825")
        self.phase_val_lbl.pack()

        # Attempt Counter
        m2 = tk.Frame(metrics_grid, bg="#181825", padx=8, pady=6)
        m2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Label(m2, text="Attempt", font=("Segoe UI", 8), fg="#a6adc8", bg="#181825").pack()
        self.attempt_val_lbl = tk.Label(m2, text="1", font=("Segoe UI", 13, "bold"), fg="#f8f8f2", bg="#181825")
        self.attempt_val_lbl.pack()

        # Retries Counter
        m3 = tk.Frame(metrics_grid, bg="#181825", padx=8, pady=6)
        m3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        tk.Label(m3, text="Retries", font=("Segoe UI", 8), fg="#a6adc8", bg="#181825").pack()
        self.retries_val_lbl = tk.Label(m3, text="0", font=("Segoe UI", 13, "bold"), fg="#f8f8f2", bg="#181825")
        self.retries_val_lbl.pack()

        # Right Column: Current Activity & Live Activity Log
        right_col = tk.Frame(content_split, bg="#1e1e2e")
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Current Activity Banner
        activity_card = tk.Frame(right_col, bg="#252538", padx=14, pady=10)
        activity_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            activity_card,
            text="CURRENT ACTIVITY",
            font=("Segoe UI", 9, "bold"),
            fg="#818cf8",
            bg="#252538",
        ).pack(anchor="w")

        self.activity_lbl = tk.Label(
            activity_card,
            text="Initializing environment and project workspace...",
            font=("Segoe UI", 10),
            fg="#cdd6f4",
            bg="#252538",
            wraplength=550,
            justify=tk.LEFT,
        )
        self.activity_lbl.pack(anchor="w", pady=(2, 0))

        # Live Activity Log Card
        log_card = tk.Frame(right_col, bg="#252538", padx=14, pady=10)
        log_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            log_card,
            text="LIVE ACTIVITY LOG",
            font=("Segoe UI", 9, "bold"),
            fg="#818cf8",
            bg="#252538",
        ).pack(anchor="w", pady=(0, 6))

        # Scrolled Text for Log
        log_frame = tk.Frame(log_card, bg="#181825")
        log_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            bg="#181825",
            fg="#cdd6f4",
            font=("Consolas", 9),
            padx=10,
            pady=8,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Configure Log Tags for color-coding
        self.log_text.tag_configure("timestamp", foreground="#6c7086")
        self.log_text.tag_configure("INFO", foreground="#89b4fa")
        self.log_text.tag_configure("SUCCESS", foreground="#a6e3a1")
        self.log_text.tag_configure("WARNING", foreground="#f9e2af")
        self.log_text.tag_configure("ERROR", foreground="#f38ba8")
        self.log_text.tag_configure("msg", foreground="#cdd6f4")

        # ----------------- Bottom Action Bar (revealed on completion/failure) -----------------
        self.bottom_bar = tk.Frame(container, bg="#252538", padx=16, pady=10)
        # Pack only when completed or failed

        self.bottom_status_lbl = tk.Label(
            self.bottom_bar,
            text="PROJECT COMPLETED ✓",
            font=("Segoe UI", 11, "bold"),
            fg="#22c55e",
            bg="#252538",
        )
        self.bottom_status_lbl.pack(side=tk.LEFT)

        btn_box = tk.Frame(self.bottom_bar, bg="#252538")
        btn_box.pack(side=tk.RIGHT)

        self.view_report_btn = tk.Button(
            btn_box,
            text="📋 View Project Handoff",
            font=("Segoe UI", 9, "bold"),
            bg="#6366f1",
            fg="#ffffff",
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.on_view_report,
        )
        self.view_report_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.open_folder_btn = tk.Button(
            btn_box,
            text="📁 Open Project Folder",
            font=("Segoe UI", 9, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.on_open_folder,
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.new_project_btn = tk.Button(
            btn_box,
            text="➕ Start New Project",
            font=("Segoe UI", 9, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.on_new_project,
        )
        self.new_project_btn.pack(side=tk.LEFT)

    def init_dashboard(self, project_name: str):
        """Initialize the dashboard when a new project run begins."""
        self.project_name_lbl.configure(text=f"Project: {project_name}")
        self.workspace_lbl.configure(text="Workspace: Creating...")
        self.status_badge.configure(text="RUNNING", bg="#3b82f6")
        self.activity_lbl.configure(text="Initializing project setup...")
        self.bottom_bar.pack_forget()

        # Reset stages to pending
        for stage_id, widgets in self.stage_widgets.items():
            widgets["icon"].configure(text="○", fg="#6c7086")
            widgets["status"].configure(text="Pending", fg="#6c7086")
            widgets["name"].configure(fg="#cdd6f4")

        # Reset counters
        self.phase_count = 1
        self.attempt_count = 1
        self.retry_count = 0
        self.phase_val_lbl.configure(text="1")
        self.attempt_val_lbl.configure(text="1")
        self.retries_val_lbl.configure(text="0")

        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def set_stage_status(self, stage_id: str, status: str):
        """Update a stage indicator to Pending, Running, Completed, or Failed."""
        if stage_id not in self.stage_widgets:
            return

        w = self.stage_widgets[stage_id]
        if status == "RUNNING":
            w["icon"].configure(text="●", fg="#38bdf8")
            w["status"].configure(text="Running", fg="#38bdf8")
            w["name"].configure(fg="#ffffff")
        elif status == "COMPLETED":
            w["icon"].configure(text="✓", fg="#22c55e")
            w["status"].configure(text="Completed", fg="#22c55e")
            w["name"].configure(fg="#cdd6f4")
        elif status == "FAILED":
            w["icon"].configure(text="✗", fg="#ef4444")
            w["status"].configure(text="Failed", fg="#ef4444")
            w["name"].configure(fg="#f87171")
        else:  # PENDING
            w["icon"].configure(text="○", fg="#6c7086")
            w["status"].configure(text="Pending", fg="#6c7086")
            w["name"].configure(fg="#6c7086")

    def handle_event(self, event: OrchestratorEvent):
        """Process an OrchestratorEvent and update dashboard widgets accordingly."""
        # 1. Update activity text
        self.activity_lbl.configure(text=event.message)

        # 2. Update phase / attempt / retries counters
        if event.phase > 0:
            self.phase_count = event.phase
            self.phase_val_lbl.configure(text=str(self.phase_count))

        if event.attempt > 0:
            self.attempt_count = event.attempt
            self.attempt_val_lbl.configure(text=str(self.attempt_count))

        if event.event_type == EventType.RETRY_PHASE:
            self.retry_count += 1
            self.retries_val_lbl.configure(text=str(self.retry_count))

        # 3. Update stage indicator if mapped
        if event.event_type in self.EVENT_STAGE_MAP:
            stage_id, stage_st = self.EVENT_STAGE_MAP[event.event_type]
            self.set_stage_status(stage_id, stage_st)

        # 4. Handle workspace path detection
        if event.event_type == EventType.PROJECT_WORKSPACE_CREATED and event.data:
            path = event.data.get("project_path", "")
            if path:
                self.workspace_lbl.configure(text=f"Workspace: {path}")

        # 5. Append to activity log
        self.append_log(event)

        # 6. Handle terminal events
        if event.event_type == EventType.PROJECT_COMPLETED:
            self.set_completed(success=True, message="PROJECT COMPLETED & READY ✓")
        elif event.event_type in (EventType.PROJECT_FAILED, EventType.PROJECT_BLOCKED):
            self.set_completed(success=False, message=f"PROJECT {event.event_type.value} ✗")

    def append_log(self, event: OrchestratorEvent):
        """Append a color-coded log entry with timestamp and level."""
        self.log_text.configure(state=tk.NORMAL)
        ts = f"[{event.timestamp}] "
        lvl = f"{event.level.upper():<7} "
        msg = f"{event.message}\n"

        self.log_text.insert(tk.END, ts, "timestamp")
        self.log_text.insert(tk.END, lvl, event.level.upper())
        self.log_text.insert(tk.END, msg, "msg")

        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def set_completed(self, success: bool, message: str):
        """Show bottom action bar when project execution terminates."""
        if success:
            self.status_badge.configure(text="COMPLETED", bg="#22c55e")
            self.bottom_status_lbl.configure(text=message, fg="#22c55e")
        else:
            self.status_badge.configure(text="FAILED", bg="#ef4444")
            self.bottom_status_lbl.configure(text=message, fg="#ef4444")

        self.bottom_bar.pack(fill=tk.X, pady=(12, 0))
