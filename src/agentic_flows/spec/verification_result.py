from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class VerificationResult:
    status: str
    reason: str
    violations: List[str]
    verified_artifact_ids: List[str]


__all__ = ["VerificationResult"]
