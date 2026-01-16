from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ReasoningStep:
    step_id: str
    input_claims: List[str]
    output_claims: List[str]
    method: str


__all__ = ["ReasoningStep"]
