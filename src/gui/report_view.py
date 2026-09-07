import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional


class ReportDialog(tk.Toplevel):
    """
    Read-only dialog window displaying the final project report.
    """

    def __init__(
        self,
        parent: tk.Widget,
        report_content: str,
        report_path: Optional[str] = None,
        title: str = "Final Project Report",
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("760x640")
        self.minsize(500, 400)
        self.configure(bg="#1e1e2e")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets(report_content, report_path)
        self.center_on_parent(parent)

    def center_on_parent(self, parent: tk.Widget):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        w = self.winfo_width()
        h = self.winfo_height()

        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _create_widgets(self, report_content: str, report_path: Optional[str]):
        # Header bar
        header_frame = tk.Frame(self, bg="#252538", padx=16, pady=12)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="PROJECT FINAL COMPLETION REPORT",
            font=("Segoe UI", 12, "bold"),
            fg="#f8f8f2",
            bg="#252538",
        )
        title_lbl.pack(anchor="w")

        if report_path:
            path_lbl = tk.Label(
                header_frame,
                text=f"Location: {report_path}",
                font=("Segoe UI", 9),
                fg="#a6adc8",
                bg="#252538",
            )
            path_lbl.pack(anchor="w", pady=(2, 0))

        # Main text container with scrollbar
        content_frame = tk.Frame(self, bg="#1e1e2e", padx=16, pady=12)
        content_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(
            content_frame,
            wrap=tk.WORD,
            bg="#181825",
            fg="#cdd6f4",
            insertbackground="#f8f8f2",
            selectbackground="#45475a",
            selectforeground="#ffffff",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)

        # Insert report text
        self.text_area.insert("1.0", report_content)
        self.text_area.configure(state=tk.DISABLED)

        # Footer actions
        footer_frame = tk.Frame(self, bg="#252538", padx=16, pady=10)
        footer_frame.pack(fill=tk.X)

        copy_btn = tk.Button(
            footer_frame,
            text="Copy Report to Clipboard",
            font=("Segoe UI", 9, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self._copy_to_clipboard(report_content),
        )
        copy_btn.pack(side=tk.LEFT)

        close_btn = tk.Button(
            footer_frame,
            text="Close",
            font=("Segoe UI", 9, "bold"),
            bg="#6366f1",
            fg="#ffffff",
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.destroy,
        )
        close_btn.pack(side=tk.RIGHT)

    def _copy_to_clipboard(self, content: str):
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "Report content copied to clipboard!", parent=self)
