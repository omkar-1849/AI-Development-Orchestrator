from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ReviewResult:
    review_id: str
    decision: str
    phase_completed: int
    summary: str
    issues: List[str]
    next_action: str
    next_phase: Optional[dict]