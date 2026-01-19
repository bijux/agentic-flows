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
from agentic_flows.spec.ontology.ids import RunID, TenantID


class ExecutionStoreProtocol(Protocol):
    def save_run(
        self,
        *,
        trace: ExecutionTrace | None,
        plan: ExecutionSteps,
        mode: RunMode,
    ) -> RunID: ...

    def save_steps(
        self, *, run_id: RunID, tenant_id: TenantID, plan: ExecutionSteps
    ) -> None: ...

    def save_events(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        events: tuple[ExecutionEvent, ...],
    ) -> None: ...

    def save_artifacts(self, *, run_id: RunID, artifacts: list[Artifact]) -> None: ...

    def save_evidence(
        self, *, run_id: RunID, evidence: list[RetrievedEvidence]
    ) -> None: ...

    def save_entropy_usage(
        self, *, run_id: RunID, usage: tuple[EntropyUsage, ...]
    ) -> None: ...

    def save_tool_invocations(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        tool_invocations: tuple[ToolInvocation, ...],
    ) -> None: ...

    def register_dataset(self, dataset: DatasetDescriptor) -> None: ...

    def load_trace(self, run_id: RunID, *, tenant_id: TenantID) -> ExecutionTrace: ...

    def load_replay_envelope(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> ReplayEnvelope: ...

    def load_dataset_descriptor(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> DatasetDescriptor: ...


__all__ = ["ExecutionStoreProtocol"]
