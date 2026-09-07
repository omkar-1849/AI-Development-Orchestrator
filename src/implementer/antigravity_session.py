from dataclasses import dataclass


@dataclass
class AntigravitySession:
    session_id: str | None = None
    connected: bool = False