from .prompt_builder import ImplementerPromptBuilder


class ImplementerManager:

    def __init__(self, implementer, session, phase_state):
        self.implementer = implementer
        self.session = session
        self.phase_state = phase_state

    def execute_task(self, worker_task, retry_feedback=None, attempt_number=1):

        report_path = self.phase_state.get_report_path()

        if not self.session.initialized:
            prompt = ImplementerPromptBuilder.build_initial_prompt(
                self.session.project_name,
                self.session.project_path,
                worker_task,
                report_path
            )

            self.session.initialized = True

        elif retry_feedback:
            prompt = ImplementerPromptBuilder.build_retry_prompt(
                worker_task,
                report_path,
                retry_feedback,
                attempt_number
            )

        else:
            prompt = ImplementerPromptBuilder.build_task_prompt(
                worker_task,
                report_path
            )

        print("\n--- REPORT EXPECTED ---")
        print(report_path)

        print("\n--- PROMPT BEING SENT TO ANTIGRAVITY ---\n")
        print(prompt)
        print("\n-----------------------------------------\n")

        return self.implementer.execute(prompt)