from src.state.phase_state import PhaseState


def test_phase_state():

    phase = PhaseState(
        project_name="CalculatorProject"
    )

    print("\n--- INITIAL STATE ---")
    print("Phase:", phase.current_phase)
    print("Attempt:", phase.current_attempt)
    print("Report:", phase.get_report_path())

    phase.next_attempt()

    print("\n--- AFTER RETRY ---")
    print("Phase:", phase.current_phase)
    print("Attempt:", phase.current_attempt)
    print("Report:", phase.get_report_path())

    phase.next_phase()

    print("\n--- AFTER NEXT PHASE ---")
    print("Phase:", phase.current_phase)
    print("Attempt:", phase.current_attempt)
    print("Report:", phase.get_report_path())


if __name__ == "__main__":
    test_phase_state()