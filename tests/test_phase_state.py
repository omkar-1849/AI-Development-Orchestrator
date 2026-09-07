import unittest

from src.state.phase_state import PhaseState


class TestPhaseState(unittest.TestCase):

    def test_initial_state(self):
        phase = PhaseState(project_name="CalculatorProject")
        self.assertEqual(phase.current_phase, 1)
        self.assertEqual(phase.current_attempt, 1)
        self.assertEqual(phase.get_report_path(), "reports/phase_1_attempt_1.md")

    def test_next_attempt(self):
        phase = PhaseState(project_name="CalculatorProject")
        phase.next_attempt()
        self.assertEqual(phase.current_phase, 1)
        self.assertEqual(phase.current_attempt, 2)
        self.assertEqual(phase.get_report_path(), "reports/phase_1_attempt_2.md")

    def test_next_phase(self):
        phase = PhaseState(project_name="CalculatorProject")
        phase.next_attempt()  # attempt 2
        phase.next_phase()    # should advance phase to 2 and reset attempt to 1
        self.assertEqual(phase.current_phase, 2)
        self.assertEqual(phase.current_attempt, 1)
        self.assertEqual(phase.get_report_path(), "reports/phase_2_attempt_1.md")

    def test_can_retry(self):
        phase = PhaseState(project_name="CalculatorProject", max_attempts=3)
        self.assertTrue(phase.can_retry())  # attempt 1
        phase.next_attempt()
        self.assertTrue(phase.can_retry())  # attempt 2
        phase.next_attempt()
        self.assertFalse(phase.can_retry())  # attempt 3 is max


if __name__ == "__main__":
    unittest.main()