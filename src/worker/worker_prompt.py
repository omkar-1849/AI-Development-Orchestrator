"""
[DEPRECATED] build_worker_prompt is legacy code from the earlier Claude-as-Worker architecture.
It has been moved to src.worker._legacy.worker_prompt.
The current orchestrator uses ImplementerPromptBuilder in src.implementer.prompt_builder.
"""

from src.worker._legacy.worker_prompt import build_worker_prompt

__all__ = ["build_worker_prompt"]