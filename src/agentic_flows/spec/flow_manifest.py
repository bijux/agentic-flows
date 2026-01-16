from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass
class FlowManifest:
    flow_id: str
    agents: Tuple[str, ...]
    dependencies: Tuple[str, ...]
    retrieval_contracts: Tuple[str, ...]
    verification_gates: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.flow_id, str) or not self.flow_id.strip():
            raise ValueError("flow_id must be a non-empty string")
        self._require_tuple_of_str("agents", self.agents)
        self._require_tuple_of_str("dependencies", self.dependencies)
        self._require_tuple_of_str("retrieval_contracts", self.retrieval_contracts)
        self._require_tuple_of_str("verification_gates", self.verification_gates)

    @staticmethod
    def _require_tuple_of_str(field: str, value: Iterable[str]) -> None:
        if not isinstance(value, tuple):
            raise ValueError(f"{field} must be a tuple of strings")
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise ValueError(f"{field} must contain non-empty strings")


__all__ = ["FlowManifest"]
