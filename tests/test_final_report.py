import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.reporting.final_report_generator import (
    PhaseRecord,
    ProjectExecutionSummary,
    generate_final_report,
    save_final_report,
)


class TestFinalReportGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_and_save_final_report(self):
        summary = ProjectExecutionSummary(
            project_name="DemoApp",
            project_path=self.temp_dir,
            original_requirements="Build a full CRUD API with FastAPI.",
        )

        summary.phase_history.append(
            PhaseRecord(
                phase_number=1,
                attempts=1,
                objective="Create core models and database",
                final_decision="APPROVED",
                status="COMPLETED",
                summary="Models and migrations set up successfully",
                issues=[],
                report_files=["reports/phase_1_attempt_1.md"],
            )
        )
        summary.phase_history.append(
            PhaseRecord(
                phase_number=2,
                attempts=2,
                objective="Add authentication endpoints",
                final_decision="APPROVED",
                status="COMPLETED",
                summary="Auth routes working and verified",
                issues=[],
                report_files=["reports/phase_2_attempt_1.md", "reports/phase_2_attempt_2.md"],
            )
        )
        summary.phases_completed = 2
        summary.total_attempts = 3
        summary.total_retries = 1
        summary.mark_completed("SUCCESSFULLY COMPLETED")

        content = generate_final_report(summary)

        # Verify content contains all required sections
        self.assertIn("# Final Project Report: DemoApp", content)
        self.assertIn("## 1. Project Information", content)
        self.assertIn("DemoApp", content)
        self.assertIn("## 2. Original Requirements", content)
        self.assertIn("Build a full CRUD API with FastAPI.", content)
        self.assertIn("## 3. Execution Summary", content)
        self.assertIn("Total Phases Completed:** 2", content)
        self.assertIn("Total Implementation Attempts:** 3", content)
        self.assertIn("Total Retries:** 1", content)
        self.assertIn("## 4. Phase History", content)
        self.assertIn("### Phase 1", content)
        self.assertIn("### Phase 2", content)
        self.assertIn("## 5. Review Summary", content)
        self.assertIn("Total Approvals:** 2", content)
        self.assertIn("## 6. Files and Artifacts", content)
        self.assertIn("## 7. Final Outcome", content)
        self.assertIn("PROJECT STATUS: SUCCESSFULLY COMPLETED", content)

        # Test save to disk
        report_file = save_final_report(summary, target_dir=self.temp_dir)
        self.assertTrue(report_file.exists())
        self.assertEqual(report_file.name, "final_project_report.md")

        with open(report_file, "r", encoding="utf-8") as f:
            disk_content = f.read()
        self.assertEqual(disk_content, content)

    def test_generate_report_with_blocked_status(self):
        summary = ProjectExecutionSummary(
            project_name="BlockedApp",
            project_path=self.temp_dir,
            original_requirements="Some requirements",
        )
        summary.phase_history.append(
            PhaseRecord(
                phase_number=1,
                attempts=1,
                objective="Initial setup",
                final_decision="BLOCKED",
                status="FAILED",
                summary="External API is down",
                issues=["Cannot connect to host"],
            )
        )
        summary.mark_completed("BLOCKED", error="External API is down")

        content = generate_final_report(summary)
        self.assertIn("PROJECT STATUS: BLOCKED", content)
        self.assertIn("External API is down", content)


if __name__ == "__main__":
    unittest.main()
