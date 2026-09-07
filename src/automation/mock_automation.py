from .automation_interface import AutomationInterface
from .automation_result import AutomationResult


class MockAutomation(AutomationInterface):

    def execute(self, prompt):
        print("\n--- AUTOMATION RECEIVED PROMPT ---")
        print(prompt)
        print("--- END PROMPT ---\n")

        return AutomationResult(
            success=True,
            output="Mock automation completed"
        )