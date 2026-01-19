# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.ontology.ids import EnvironmentFingerprint, FlowID, PlanHash
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    ReplayAcceptability,
)


@dataclass(frozen=True)
class ExecutionSteps:
    spec_version: str
    flow_id: FlowID
    determinism_level: DeterminismLevel
    replay_acceptability: ReplayAcceptability
    entropy_budget: EntropyBudget
    steps: tuple[ResolvedStep, ...]
    environment_fingerprint: EnvironmentFingerprint
    plan_hash: PlanHash
    resolution_metadata: tuple[tuple[str, str], ...]


__all__ = ["ExecutionSteps"]
