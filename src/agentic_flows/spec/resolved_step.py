from dataclasses import dataclass
from typing import List, Optional

from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.retrieval_request import RetrievalRequest


@dataclass(frozen=True)
class ResolvedStep:
    step_index: int
    agent_id: str
    inputs_fingerprint: str
    declared_dependencies: List[str]
    expected_artifacts: List[str]
    agent_invocation: AgentInvocation
    retrieval_request: Optional[RetrievalRequest]


__all__ = ["ResolvedStep"]
