from abc import ABC, abstractmethod


class AutomationInterface(ABC):

    @abstractmethod
    def execute(self, prompt):
        """
        Send prompt to the external application.

        Returns:
            AutomationResult
        """

        pass