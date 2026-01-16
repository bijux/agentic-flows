from dataclasses import dataclass
from typing import List

from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep


@dataclass(frozen=True)
class ReasoningBundle:
    bundle_id: str
    claims: List[ReasoningClaim]
    steps: List[ReasoningStep]
    evidence_ids: List[str]
    producer_agent_id: str


__all__ = ["ReasoningBundle"]
