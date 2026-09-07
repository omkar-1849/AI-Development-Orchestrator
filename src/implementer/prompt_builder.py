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