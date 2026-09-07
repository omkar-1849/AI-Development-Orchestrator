from src.state.workflow_state import WorkflowState


class StateManager:

    def __init__(self):
        self.current_state = WorkflowState.IDLE

    def transition(self, new_state):

        print(
            f"Workflow state changed: "
            f"{self.current_state.name} -> {new_state.name}"
        )

        self.current_state = new_state