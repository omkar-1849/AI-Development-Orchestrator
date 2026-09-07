from dataclasses import dataclass
from typing import Optional


@dataclass
class AutomationResult:
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None