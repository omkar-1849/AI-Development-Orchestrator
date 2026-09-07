from .implementer_interface import ImplementerInterface
from .implementer_result import ImplementerResult


class AntigravityAdapter(ImplementerInterface):

    def __init__(self, automation):
        self.automation = automation

    def execute(self, prompt):

        try:
            result = self.automation.execute(prompt)

            if not result.success:
                return ImplementerResult(
                    success=False,
                    message="Antigravity execution failed",
                    error=result.error
                )

            return ImplementerResult(
                success=True,
                message="Prompt sent to Antigravity successfully",
                output=result.output
            )

        except Exception as e:
            return ImplementerResult(
                success=False,
                message="Antigravity execution failed",
                error=str(e)
            )