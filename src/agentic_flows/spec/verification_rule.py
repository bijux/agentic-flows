from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationRule:
    rule_id: str
    description: str
    severity: str
    target: str


__all__ = ["VerificationRule"]
