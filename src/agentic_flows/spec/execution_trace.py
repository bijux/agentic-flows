from dataclasses import dataclass
from typing import List

from agentic_flows.spec.execution_event import ExecutionEvent


@dataclass(frozen=True)
class ExecutionTrace:
    flow_id: str
    environment_fingerprint: str
    resolver_id: str
    events: List[ExecutionEvent]


__all__ = ["ExecutionTrace"]
