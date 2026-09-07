"""
[DEPRECATED] AntigravitySession is an unused legacy session dataclass.
The active implementation uses ImplementerSession in src.implementer.implementer_session.
"""

from dataclasses import dataclass


@dataclass
class AntigravitySession:
    session_id: str | None = None
    connected: bool = False