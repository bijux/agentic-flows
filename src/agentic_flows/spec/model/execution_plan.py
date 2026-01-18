# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.ontology.ids import EnvironmentFingerprint, FlowID, PlanHash


@dataclass(frozen=True)
class ExecutionPlan:
    spec_version: str
    flow_id: FlowID
    steps: tuple[ResolvedStep, ...]
    environment_fingerprint: EnvironmentFingerprint
    plan_hash: PlanHash
    resolution_metadata: tuple[tuple[str, str], ...]


__all__ = ["ExecutionPlan"]
