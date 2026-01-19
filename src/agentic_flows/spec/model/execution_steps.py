# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    TenantID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    FlowState,
    ReplayAcceptability,
)


@dataclass(frozen=True)
class ExecutionSteps:
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
    steps: tuple[ResolvedStep, ...]
    environment_fingerprint: EnvironmentFingerprint
    plan_hash: PlanHash
    resolution_metadata: tuple[tuple[str, str], ...]


__all__ = ["ExecutionSteps"]
