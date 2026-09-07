"""
[DEPRECATED] validate_worker_response is legacy code from the earlier Claude-as-Worker architecture.
It has been moved to src.worker._legacy.worker_validator.
The current orchestrator uses Reviewer validation and ImplementerResult.
"""

from src.worker._legacy.worker_validator import (
    WorkerValidationError,
    validate_worker_response,
)

__all__ = ["WorkerValidationError", "validate_worker_response"]