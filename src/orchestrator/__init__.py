# Orchestrator package
#
# Heavy modules (pipeline, phase_runner, setup) are imported directly
# from their modules to avoid loading Windows automation dependencies
# when only lightweight components (events, etc.) are needed.
#
# Usage:
#   from src.orchestrator.events import EventType
#   from src.orchestrator.pipeline import run_orchestrator
#   from src.orchestrator.phase_runner import run_phase
#   from src.orchestrator.setup import setup_orchestrator
