from dataclasses import dataclass
from typing import List, Tuple

from agentic_flows.spec.resolved_step import ResolvedStep


@dataclass(frozen=True)
class ExecutionPlan:
    flow_id: str
    steps: List[ResolvedStep]
    environment_fingerprint: str
    resolution_metadata: Tuple[Tuple[str, str], ...]


__all__ = ["ExecutionPlan"]
