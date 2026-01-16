from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AgentInvocation:
    agent_id: str
    agent_version: str
    inputs_fingerprint: str
    declared_outputs: List[str]
    execution_mode: str


__all__ = ["AgentInvocation"]
