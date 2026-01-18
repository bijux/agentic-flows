# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from agentic_flows.spec.ids import AgentID, ContractID, FlowID, GateID


# NOTE: This manifest defines structure only.
# Semantic validity is enforced elsewhere.
@dataclass
class FlowManifest:
    spec_version: str
    flow_id: FlowID
    agents: tuple[AgentID, ...]
    dependencies: tuple[str, ...]
    retrieval_contracts: tuple[ContractID, ...]
    verification_gates: tuple[GateID, ...]

    def __post_init__(self) -> None:
        # TODO: Enforce determinism obligations for manifest inputs.
        # TODO: Verify dependency completeness and dependency closure.
        # TODO: Enforce artifact guarantees declared by the flow.
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
