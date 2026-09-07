from dataclasses import dataclass
from typing import Optional


@dataclass
class ImplementerResult:
    """
    Standard result returned by implementation agents.
    """

    success: bool

    message: str

    output: Optional[str] = None

    error: Optional[str] = None