from dataclasses import dataclass
from typing import List, Tuple

from agentic_flows.spec.verification_rule import VerificationRule


@dataclass
class VerificationPolicy:
    verification_level: str
    failure_mode: str
    required_evidence: Tuple[str, ...]
    rules: List[VerificationRule]
    fail_on: List[str]
    escalate_on: List[str]


__all__ = ["VerificationPolicy"]
