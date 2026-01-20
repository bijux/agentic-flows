# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from typing import Protocol

from agentic_flows.runtime.context import RunMode
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.ontology.ids import ClaimID, RunID, TenantID


class ExecutionWriteStoreProtocol(Protocol):
    """Write store protocol; misuse breaks persistence guarantees."""

    def begin_run(
        self,
        *,
        plan: ExecutionSteps,
        mode: RunMode,
    ) -> RunID: ...

    def finalize_run(self, *, run_id: RunID, trace: ExecutionTrace) -> None: ...

    def save_steps(
        self, *, run_id: RunID, tenant_id: TenantID, plan: ExecutionSteps
    ) -> None: ...

    def save_checkpoint(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        step_index: int,
        event_index: int,
    ) -> None: ...

    def save_events(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        events: tuple[ExecutionEvent, ...],
    ) -> None: ...

    def save_artifacts(self, *, run_id: RunID, artifacts: list[Artifact]) -> None: ...

    def append_evidence(
        self,
        *,
        run_id: RunID,
        evidence: list[RetrievedEvidence],
        starting_index: int,
    ) -> None: ...

    def append_entropy_usage(
        self,
        *,
        run_id: RunID,
        usage: tuple[EntropyUsage, ...],
        starting_index: int,
    ) -> None: ...

    def append_tool_invocations(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        tool_invocations: tuple[ToolInvocation, ...],
        starting_index: int,
    ) -> None: ...

    def append_claim_ids(
        self, *, run_id: RunID, tenant_id: TenantID, claim_ids: tuple[ClaimID, ...]
    ) -> None: ...

    def register_dataset(self, dataset: DatasetDescriptor) -> None: ...


class ExecutionReadStoreProtocol(Protocol):
    """Read store protocol; misuse breaks replay guarantees."""

    def load_trace(self, run_id: RunID, *, tenant_id: TenantID) -> ExecutionTrace: ...

    def load_events(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[ExecutionEvent, ...]: ...

    def load_artifacts(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[Artifact, ...]: ...

    def load_evidence(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[RetrievedEvidence, ...]: ...

    def load_tool_invocations(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[ToolInvocation, ...]: ...

    def load_entropy_usage(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[EntropyUsage, ...]: ...

    def load_claim_ids(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[ClaimID, ...]: ...

    def load_checkpoint(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[int, int] | None: ...

    def load_replay_envelope(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> ReplayEnvelope: ...

    def load_dataset_descriptor(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> DatasetDescriptor: ...


__all__ = ["ExecutionReadStoreProtocol", "ExecutionWriteStoreProtocol"]
