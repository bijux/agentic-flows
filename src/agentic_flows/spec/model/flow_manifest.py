# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for spec/model/flow_manifest.py."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.artifact.entropy_budget import EntropyBudget
from agentic_flows.spec.model.datasets.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.execution.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology import (
    DeterminismLevel,
    FlowState,
)
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    FlowID,
    GateID,
    TenantID,
)
from agentic_flows.spec.ontology.public import ReplayAcceptability


# NOTE: This manifest defines structure only.
# Semantic validity is enforced elsewhere.
@dataclass(frozen=True)
class FlowManifest:
    """Flow manifest contract; misuse breaks plan validity."""

    spec_version: str
    flow_id: FlowID
    tenant_id: TenantID
    flow_state: FlowState
    determinism_level: DeterminismLevel
    replay_acceptability: ReplayAcceptability
    entropy_budget: EntropyBudget
    replay_envelope: ReplayEnvelope
    dataset: DatasetDescriptor
    allow_deprecated_datasets: bool
    agents: tuple[AgentID, ...]
    dependencies: tuple[str, ...]
    retrieval_contracts: tuple[ContractID, ...]
    verification_gates: tuple[GateID, ...]


__all__ = ["FlowManifest"]
