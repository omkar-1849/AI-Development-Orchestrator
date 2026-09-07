import unittest
from src.orchestrator.events import (
    EventType,
    OrchestratorEvent,
    emit_event,
)


class TestOrchestratorEvents(unittest.TestCase):

    def test_create_orchestrator_event(self):
        event = OrchestratorEvent(
            event_type=EventType.PLANNER_STARTED,
            message="Planner analyzing requirements",
            phase=1,
            attempt=1,
            level="INFO",
            data={"key": "val"},
        )
        self.assertEqual(event.event_type, EventType.PLANNER_STARTED)
        self.assertEqual(event.message, "Planner analyzing requirements")
        self.assertEqual(event.phase, 1)
        self.assertEqual(event.attempt, 1)
        self.assertEqual(event.level, "INFO")
        self.assertEqual(event.data, {"key": "val"})
        self.assertTrue(bool(event.timestamp))

    def test_emit_event_with_callback(self):
        received = []

        def callback(evt):
            received.append(evt)

        event = emit_event(
            callback=callback,
            event_type=EventType.REVIEW_APPROVED,
            message="Phase approved",
            phase=2,
            attempt=1,
            level="SUCCESS",
            data={"decision": "APPROVED"},
        )

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].event_type, EventType.REVIEW_APPROVED)
        self.assertEqual(received[0].phase, 2)
        self.assertEqual(received[0].level, "SUCCESS")
        self.assertEqual(event.data["decision"], "APPROVED")

    def test_emit_event_without_callback(self):
        # Should not raise any error when callback is None
        event = emit_event(
            callback=None,
            event_type=EventType.PROJECT_WORKSPACE_CREATED,
            message="Workspace ready",
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, EventType.PROJECT_WORKSPACE_CREATED)


if __name__ == "__main__":
    unittest.main()
