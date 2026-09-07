"""
[DEPRECATED] WorkerResponse is legacy code from the earlier Claude-as-Worker architecture.
It has been moved to src.worker._legacy.worker_response.
The current orchestrator uses AntigravityAdapter and ImplementerResult.
"""

from src.worker._legacy.worker_response import WorkerResponse

__all__ = ["WorkerResponse"]