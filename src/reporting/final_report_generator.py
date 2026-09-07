import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PhaseRecord:
    phase_number: int
    attempts: int
    objective: str
    final_decision: str  # APPROVED, CORRECTION_NEEDED, BLOCKED, REPLAN
    status: str  # COMPLETED, RETRIED, FAILED
    summary: str = ""
    issues: List[str] = field(default_factory=list)
    report_files: List[str] = field(default_factory=list)


@dataclass
class ProjectExecutionSummary:
    project_name: str
    project_path: str
    original_requirements: str
    started_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    completed_at: Optional[str] = None
    final_status: str = "IN_PROGRESS"  # SUCCESSFULLY COMPLETED, BLOCKED, STOPPED, FAILED
    phases_completed: int = 0
    total_attempts: int = 0
    total_retries: int = 0
    phase_history: List[PhaseRecord] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def mark_completed(self, status: str = "SUCCESSFULLY COMPLETED", error: Optional[str] = None):
        self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.final_status = status
        if error:
            self.error_message = error

    def compute_review_summary(self) -> Dict[str, Any]:
        approvals = sum(1 for p in self.phase_history if p.final_decision == "APPROVED")
        retries = self.total_retries
        blockers = [p.summary for p in self.phase_history if p.final_decision == "BLOCKED"]
        if self.error_message and self.final_status in ("BLOCKED", "FAILED"):
            blockers.append(self.error_message)

        return {
            "approvals": approvals,
            "retries": retries,
            "blockers": blockers,
            "final_reviewer_status": (
                "APPROVED" if self.final_status == "SUCCESSFULLY COMPLETED" else self.final_status
            ),
        }


def generate_final_report(summary: ProjectExecutionSummary) -> str:
    """
    Generate a comprehensive Markdown project-level final report
    summarizing the entire orchestration lifecycle.
    """
    review_stats = summary.compute_review_summary()
    completed_time = summary.completed_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# Final Project Report: {summary.project_name}",
        "",
        "## 1. Project Information",
        "",
        f"- **Project Name:** {summary.project_name}",
        f"- **Project Path:** `{summary.project_path}`",
        f"- **Start Time:** {summary.started_at}",
        f"- **End Time:** {completed_time}",
        f"- **Final Status:** {summary.final_status}",
        "",
        "## 2. Original Requirements",
        "",
        "```text",
        summary.original_requirements.strip() if summary.original_requirements else "(None provided)",
        "```",
        "",
        "## 3. Execution Summary",
        "",
        f"- **Total Phases Completed:** {summary.phases_completed}",
        f"- **Total Implementation Attempts:** {summary.total_attempts}",
        f"- **Total Retries:** {summary.total_retries}",
        f"- **Final Workflow Result:** {summary.final_status}",
        "",
        "## 4. Phase History",
        "",
    ]

    if not summary.phase_history:
        lines.append("_No phases were executed._\n")
    else:
        for phase in summary.phase_history:
            lines.extend([
                f"### Phase {phase.phase_number}",
                f"- **Objective:** {phase.objective or 'N/A'}",
                f"- **Attempts:** {phase.attempts}",
                f"- **Final Decision:** {phase.final_decision}",
                f"- **Status:** {phase.status}",
            ])
            if phase.summary:
                lines.append(f"- **Summary:** {phase.summary}")
            if phase.issues:
                lines.append(f"- **Issues:** {', '.join(phase.issues)}")
            if phase.report_files:
                lines.append(f"- **Phase Reports:** {', '.join(f'`{r}`' for r in phase.report_files)}")
            lines.append("")

    lines.extend([
        "## 5. Review Summary",
        "",
        f"- **Total Approvals:** {review_stats['approvals']}",
        f"- **Total Retries:** {review_stats['retries']}",
        f"- **Final Reviewer Status:** {review_stats['final_reviewer_status']}",
    ])

    if review_stats["blockers"]:
        lines.append("- **Blockers Identified:**")
        for blocker in review_stats["blockers"]:
            lines.append(f"  - {blocker}")
    else:
        lines.append("- **Blockers Identified:** None")
    lines.append("")

    lines.extend([
        "## 6. Files and Artifacts",
        "",
        f"- **Workspace Path:** `{summary.project_path}`",
    ])

    # Discover reports if present
    reports_dir = Path(summary.project_path) / "reports"
    discovered_reports = []
    if reports_dir.exists() and reports_dir.is_dir():
        discovered_reports = sorted([f.name for f in reports_dir.glob("*.md")])

    all_artifacts = sorted(list(set(summary.artifacts + [f"reports/{r}" for r in discovered_reports])))
    if all_artifacts:
        lines.append("- **Generated Artifacts & Reports:**")
        for art in all_artifacts:
            lines.append(f"  - `{art}`")
    else:
        lines.append("- **Generated Artifacts & Reports:** None")
    lines.append("")

    lines.extend([
        "## 7. Final Outcome",
        "",
        f"**PROJECT STATUS: {summary.final_status}**",
    ])
    if summary.error_message:
        lines.extend([
            "",
            f"**Error Details:** {summary.error_message}",
        ])
    lines.append("")

    return "\n".join(lines)


def save_final_report(
    summary: ProjectExecutionSummary,
    target_dir: Optional[str] = None,
) -> Path:
    """
    Generate and save `final_project_report.md` inside the project workspace directory.
    Returns the path to the written report file.
    """
    base_path = Path(target_dir or summary.project_path)
    base_path.mkdir(parents=True, exist_ok=True)

    report_path = base_path / "final_project_report.md"
    content = generate_final_report(summary)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path
