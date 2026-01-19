# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.ontology.ids import AgentID, ContractID, FlowID, GateID
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    ReplayAcceptability,
)


# NOTE: This manifest defines structure only.
# Semantic validity is enforced elsewhere.
@dataclass(frozen=True)
class FlowManifest:
    spec_version: str
    flow_id: FlowID
    determinism_level: DeterminismLevel
    replay_acceptability: ReplayAcceptability
    entropy_budget: EntropyBudget
    agents: tuple[AgentID, ...]
    dependencies: tuple[str, ...]
    retrieval_contracts: tuple[ContractID, ...]
    verification_gates: tuple[GateID, ...]


__all__ = ["FlowManifest"]
