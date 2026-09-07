from .implementer_interface import ImplementerInterface
from .implementer_result import ImplementerResult


class MockImplementer(ImplementerInterface):
    """
    Temporary implementation agent for testing.
    """

    def execute(self, worker_task):
        return ImplementerResult(
            success=True,
            message="Mock implementation completed successfully",
            output=f"Executed task: {worker_task}"
        )