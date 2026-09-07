from .automation_interface import AutomationInterface


class MockAutomation(AutomationInterface):

    def execute(self, prompt):
        print("\n--- AUTOMATION RECEIVED PROMPT ---")
        print(prompt)
        print("--- END PROMPT ---\n")

        return "Mock automation completed"