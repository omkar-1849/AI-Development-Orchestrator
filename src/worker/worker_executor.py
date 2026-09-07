"""
[DEPRECATED] execute_worker is legacy code from the earlier Claude-as-Worker architecture.
It has been moved to src.worker._legacy.worker_executor.
The current orchestrator uses ImplementerManager in src.implementer.implementer_manager.
"""

from src.worker._legacy.worker_executor import execute_worker

__all__ = ["execute_worker"]