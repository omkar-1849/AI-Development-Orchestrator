class ImplementerPromptBuilder:

    @staticmethod
    def build_initial_prompt(project_name, project_path, worker_task, report_path):
        return f"""
You are the Implementation Agent.

The project name is: {project_name}

Create and work only inside this project folder:
{project_path}

Your job is to implement the tasks provided by the AI Development Orchestrator.

IMPORTANT RULES:

- Work only inside the project folder.
- Do not modify unrelated files.
- Follow the task instructions exactly.
- Verify your work before finishing.
- Do not provide long explanations in chat.

IMPORTANT REPORT RULE:

Write the implementation report EXACTLY to:

{project_path}/{report_path}

Do not choose another report filename.
Do not overwrite reports from previous attempts.

The report must contain:

- Task ID
- Files created or modified
- Changes made
- Verification performed
- Blockers, if any

The FINAL line of the report MUST be:

<!-- REPORT_END -->

CURRENT TASK:

Task ID: {worker_task.task_id}

Objective:
{worker_task.objective}

Instructions:
{chr(10).join(f"- {instruction}" for instruction in worker_task.instructions)}

Files Allowed:
{chr(10).join(f"- {file}" for file in worker_task.files_allowed)}

Acceptance Criteria:
{chr(10).join(f"- {criteria}" for criteria in worker_task.acceptance_criteria)}

Start implementation now.
""".strip()

    @staticmethod
    def build_task_prompt(worker_task, report_path):
        return f"""
NEW TASK FROM ORCHESTRATOR

Task ID: {worker_task.task_id}

Objective:
{worker_task.objective}

Instructions:
{chr(10).join(f"- {instruction}" for instruction in worker_task.instructions)}

Files Allowed:
{chr(10).join(f"- {file}" for file in worker_task.files_allowed)}

Acceptance Criteria:
{chr(10).join(f"- {criteria}" for criteria in worker_task.acceptance_criteria)}

IMPORTANT:

- Continue working in the existing project folder.
- Implement only this task.
- Verify the acceptance criteria.

Write the implementation report EXACTLY to:

{report_path}

Do not choose another report filename.
Do not overwrite previous reports.

The FINAL line of the report MUST be:

<!-- REPORT_END -->

Keep the chat response concise.

Start now.
""".strip()

    @staticmethod
    def build_retry_prompt(worker_task, report_path, retry_feedback, attempt_number):
        issues_text = ""
        if retry_feedback:
            numbered_issues = "\n".join(
                f"{i + 1}. {issue}"
                for i, issue in enumerate(retry_feedback)
            )
            issues_text = f"""

PREVIOUS REVIEW FEEDBACK — MUST BE FIXED

The previous implementation attempt was reviewed and corrections are required.

Issues identified:

{numbered_issues}

You must address every issue above.

Do not merely repeat the previous implementation.
Inspect the existing project state and correct the identified problems.

This is retry attempt {attempt_number}.
"""

        return f"""
RETRY TASK FROM ORCHESTRATOR

Task ID: {worker_task.task_id}

Objective:
{worker_task.objective}

Instructions:
{chr(10).join(f"- {instruction}" for instruction in worker_task.instructions)}

Files Allowed:
{chr(10).join(f"- {file}" for file in worker_task.files_allowed)}

Acceptance Criteria:
{chr(10).join(f"- {criteria}" for criteria in worker_task.acceptance_criteria)}
{issues_text}
IMPORTANT:

- Continue working in the existing project folder.
- Fix the issues identified above.
- Verify the acceptance criteria.

Write the implementation report EXACTLY to:

{report_path}

Do not choose another report filename.
Do not overwrite previous reports.

The FINAL line of the report MUST be:

<!-- REPORT_END -->

Keep the chat response concise.

Start now.
""".strip()

    @staticmethod
    def build_final_handoff_prompt(
        project_name: str,
        project_path: str,
        user_requirements: str,
        handoff_filename: str = "final_project_handoff.md",
    ) -> str:
        req_summary = user_requirements.strip() if user_requirements else "Project implementation"
        return f"""
FINAL PROJECT HANDOFF TASK

Project Name: {project_name}
Project Location: {project_path}

Context:
All development phases for this project have been successfully completed and approved by the reviewer.
Your final task is to inspect the completed project workspace and generate a concise, practical, user-facing final handoff report.

Requirements context:
{req_summary}

IMPORTANT RULES:
- Inspect the actual completed project workspace at: {project_path}
- The report is written for the END USER who wants to understand, run, and test this project.
- Do NOT generate a technical audit, code dump, architectural essay, or internal debugging logs.
- Provide simple, copy-pasteable commands for running and testing.
- Keep the tone helpful, clear, and practical.

Write the final handoff report EXACTLY to:
{project_path}/{handoff_filename}

Do not choose another filename.

The report MUST be structured in Markdown and include:
1. # Project Handoff: {project_name}
2. ## Project Location
   - Path: `{project_path}`
3. ## What Was Built (Short description/overview)
4. ## Main Features Implemented (Bulleted list)
5. ## Important Files & Entry Points (e.g., main.py, app.py, key modules)
6. ## Setup Instructions (e.g., python -m venv .venv, pip install -r requirements.txt)
7. ## How to Run (Step-by-step simple commands to launch the application)
8. ## How to Test (Command to execute tests, e.g. python -m unittest discover)
9. ## Project Status (e.g., READY TO RUN)
10. ## Important Notes (Any operational notes, prerequisites, or limitations)

The FINAL line of the report MUST be:
<!-- REPORT_END -->

Start inspecting the workspace and create {handoff_filename} now.
""".strip()