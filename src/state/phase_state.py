class PhaseState:
    def __init__(
        self,
        project_name,
        current_phase=1,
        current_attempt=1,
        max_attempts=3
    ):
        self.project_name = project_name
        self.current_phase = current_phase
        self.current_attempt = current_attempt
        self.max_attempts = max_attempts

    def next_attempt(self):
        self.current_attempt += 1

    def next_phase(self):
        self.current_phase += 1
        self.current_attempt = 1

    def can_retry(self):
        return self.current_attempt < self.max_attempts

    def get_report_filename(self):
        return (
            f"phase_{self.current_phase}"
            f"_attempt_{self.current_attempt}.md"
        )

    def get_report_path(self):
        return (
            f"reports/"
            f"{self.get_report_filename()}"
        )