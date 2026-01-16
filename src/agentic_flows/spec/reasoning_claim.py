from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ReasoningClaim:
    claim_id: str
    statement: str
    confidence: float
    supported_by: List[str]


__all__ = ["ReasoningClaim"]
