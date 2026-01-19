# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.ontology.ids import (
    ClaimID,
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    PolicyFingerprint,
    ResolverID,
    TenantID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    FlowState,
    ReplayAcceptability,
)


@dataclass(frozen=True)
class ExecutionTrace:
    spec_version: str
    flow_id: FlowID
    tenant_id: TenantID
    parent_flow_id: FlowID | None
    child_flow_ids: tuple[FlowID, ...]
    flow_state: FlowState
    determinism_level: DeterminismLevel
    replay_acceptability: ReplayAcceptability
    dataset: DatasetDescriptor
    replay_envelope: ReplayEnvelope
    allow_deprecated_datasets: bool
    environment_fingerprint: EnvironmentFingerprint
    plan_hash: PlanHash
    verification_policy_fingerprint: PolicyFingerprint | None
    resolver_id: ResolverID
    events: tuple[ExecutionEvent, ...]
    tool_invocations: tuple[ToolInvocation, ...]
    entropy_usage: tuple[EntropyUsage, ...]
    claim_ids: tuple[ClaimID, ...]
    contradiction_count: int
    arbitration_decision: str
    finalized: bool

    def finalize(self) -> ExecutionTrace:
        if object.__getattribute__(self, "finalized"):
            raise RuntimeError("ExecutionTrace already finalized")
        object.__setattr__(self, "finalized", True)
        return self

    def __getattribute__(self, name: str):
        if name in {
            "finalize",
            "__class__",
            "__dict__",
            "__getattribute__",
            "__setattr__",
        }:
            return object.__getattribute__(self, name)
        if not object.__getattribute__(self, "finalized"):
            raise RuntimeError("ExecutionTrace accessed before finalization")
        return object.__getattribute__(self, name)


__all__ = ["ExecutionTrace"]
