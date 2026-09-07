from abc import ABC, abstractmethod


class ImplementerInterface(ABC):
    """
    Base interface for all implementation agents.

    Examples:
    - Antigravity
    - Z.ai
    - Future coding agents
    """

    @abstractmethod
    def execute(self, worker_task):
        """
        Execute the implementation task.

        Args:
            worker_task:
                The validated task provided by the Worker layer.

        Returns:
            Implementation result.
        """

        pass