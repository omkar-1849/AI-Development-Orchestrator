import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class SetupView(tk.Frame):
    """
    Screen 1: Project Setup View.
    Collects Project Name and Requirements, validates input, and starts orchestration.
    """

    PLACEHOLDER_TEXT = (
        "Describe the project you want the AI development system to build...\n\n"
        "Example:\n"
        "Build a Python REST API for a task management application with SQLite storage, "
        "including endpoints for creating, listing, updating, and deleting tasks."
    )

    def __init__(
        self,
        parent: tk.Widget,
        on_start_callback: Callable[[str, str], None],
        **kwargs,
    ):
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self.on_start_callback = on_start_callback
        self._placeholder_active = True

        self._create_widgets()

    def _create_widgets(self):
        # Outer scrollable or centered container
        container = tk.Frame(self, bg="#1e1e2e", padx=30, pady=24)
        container.pack(fill=tk.BOTH, expand=True)

        # Header Title
        title_label = tk.Label(
            container,
            text="AI DEVELOPMENT ORCHESTRATOR",
            font=("Segoe UI", 20, "bold"),
            fg="#f8f8f2",
            bg="#1e1e2e",
        )
        title_label.pack(anchor="w", pady=(0, 4))

        subtitle_label = tk.Label(
            container,
            text="Autonomous Multi-Phase Software Engineering System",
            font=("Segoe UI", 10),
            fg="#a6adc8",
            bg="#1e1e2e",
        )
        subtitle_label.pack(anchor="w", pady=(0, 20))

        # Card container
        card = tk.Frame(container, bg="#252538", padx=24, pady=20, relief=tk.FLAT)
        card.pack(fill=tk.BOTH, expand=True)

        # Section Heading
        section_label = tk.Label(
            card,
            text="PROJECT SETUP",
            font=("Segoe UI", 12, "bold"),
            fg="#818cf8",
            bg="#252538",
        )
        section_label.pack(anchor="w", pady=(0, 16))

        # Project Name Field
        name_label = tk.Label(
            card,
            text="Project Name:",
            font=("Segoe UI", 10, "bold"),
            fg="#cdd6f4",
            bg="#252538",
        )
        name_label.pack(anchor="w", pady=(0, 4))

        self.name_entry = tk.Entry(
            card,
            font=("Segoe UI", 11),
            bg="#181825",
            fg="#f8f8f2",
            insertbackground="#f8f8f2",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#3b3b54",
            highlightcolor="#6366f1",
        )
        self.name_entry.pack(fill=tk.X, pady=(0, 4), ipady=5)

        name_hint = tk.Label(
            card,
            text="Use letters, numbers, spaces, hyphens, or underscores (spaces will become underscores).",
            font=("Segoe UI", 8),
            fg="#6c7086",
            bg="#252538",
        )
        name_hint.pack(anchor="w", pady=(0, 16))

        # Project Requirements Field
        req_label = tk.Label(
            card,
            text="Project Requirements:",
            font=("Segoe UI", 10, "bold"),
            fg="#cdd6f4",
            bg="#252538",
        )
        req_label.pack(anchor="w", pady=(0, 4))

        # Text area with scrollbar
        text_frame = tk.Frame(card, bg="#181825", highlightthickness=1, highlightbackground="#3b3b54")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.req_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            bg="#181825",
            fg="#6c7086",
            insertbackground="#f8f8f2",
            selectbackground="#45475a",
            selectforeground="#ffffff",
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            height=10,
        )
        self.req_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.req_text.yview)

        # Set placeholder
        self.req_text.insert("1.0", self.PLACEHOLDER_TEXT)
        self.req_text.bind("<FocusIn>", self._on_text_focus_in)
        self.req_text.bind("<FocusOut>", self._on_text_focus_out)

        # Error / Validation Message label
        self.error_label = tk.Label(
            card,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg="#f87171",
            bg="#252538",
            wraplength=700,
            justify=tk.LEFT,
        )
        self.error_label.pack(anchor="w", pady=(4, 12))

        # Action Buttons
        btn_frame = tk.Frame(card, bg="#252538")
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        self.start_btn = tk.Button(
            btn_frame,
            text="🚀  Start Project Orchestration",
            font=("Segoe UI", 11, "bold"),
            bg="#6366f1",
            fg="#ffffff",
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._on_start_clicked,
        )
        self.start_btn.pack(side=tk.RIGHT)

    def _on_text_focus_in(self, event=None):
        if self._placeholder_active:
            self.req_text.delete("1.0", tk.END)
            self.req_text.configure(fg="#cdd6f4")
            self._placeholder_active = False

    def _on_text_focus_out(self, event=None):
        content = self.req_text.get("1.0", tk.END).strip()
        if not content:
            self.req_text.delete("1.0", tk.END)
            self.req_text.insert("1.0", self.PLACEHOLDER_TEXT)
            self.req_text.configure(fg="#6c7086")
            self._placeholder_active = True

    def get_project_name(self) -> str:
        return self.name_entry.get().strip()

    def get_requirements(self) -> str:
        if self._placeholder_active:
            return ""
        return self.req_text.get("1.0", tk.END).strip()

    def show_error(self, message: str):
        self.error_label.configure(text=f"⚠️  {message}", fg="#f87171")

    def clear_error(self):
        self.error_label.configure(text="")

    def set_loading(self, loading: bool):
        if loading:
            self.start_btn.configure(
                state=tk.DISABLED,
                text="Starting Orchestration...",
                bg="#4338ca",
                cursor="watch",
            )
            self.name_entry.configure(state=tk.DISABLED)
            self.req_text.configure(state=tk.DISABLED)
        else:
            self.start_btn.configure(
                state=tk.NORMAL,
                text="🚀  Start Project Orchestration",
                bg="#6366f1",
                cursor="hand2",
            )
            self.name_entry.configure(state=tk.NORMAL)
            self.req_text.configure(state=tk.NORMAL)

    def _on_start_clicked(self):
        self.clear_error()
        name = self.get_project_name()
        reqs = self.get_requirements()

        if not name:
            self.show_error("Please provide a project name.")
            self.name_entry.focus_set()
            return

        if not reqs:
            self.show_error("Please enter project requirements before starting.")
            self.req_text.focus_set()
            return

        self.set_loading(True)
        self.on_start_callback(name, reqs)

    def reset_view(self):
        """Reset inputs and state for a fresh project setup."""
        self.name_entry.configure(state=tk.NORMAL)
        self.name_entry.delete(0, tk.END)

        self.req_text.configure(state=tk.NORMAL)
        self.req_text.delete("1.0", tk.END)
        self.req_text.insert("1.0", self.PLACEHOLDER_TEXT)
        self.req_text.configure(fg="#6c7086")
        self._placeholder_active = True

        self.clear_error()
        self.set_loading(False)
