from enum import Enum


class WorkflowState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    WAITING_FOR_RESPONSE = "WAITING_FOR_RESPONSE"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    STORED = "STORED"
    READY_FOR_WORKER = "READY_FOR_WORKER"
    ERROR = "ERROR"


class WorkflowStateManager:
    def __init__(self):
        self.current_state = WorkflowState.IDLE

    def set_state(self, new_state):
        if isinstance(new_state, str):
            new_state = WorkflowState(new_state)

        old_state = self.current_state
        self.current_state = new_state

        print(
            f"Workflow state changed: "
            f"{old_state.value} -> {new_state.value}"
        )

    def get_state(self):
        return self.current_state

    def is_state(self, state):
        if isinstance(state, str):
            state = WorkflowState(state)

        return self.current_state == state