# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.observability.execution_store_protocol import (
    ExecutionStoreProtocol,
)
from agentic_flows.runtime.observability.trace_diff import semantic_trace_diff
from agentic_flows.runtime.orchestration.determinism_guard import validate_replay
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    FlowRunResult,
    execute_flow,
)
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.ontology.ids import RunID, TenantID


def replay_with_store(
    *,
    store: ExecutionStoreProtocol,
    run_id: RunID,
    tenant_id: TenantID,
    resolved_flow: ExecutionPlan,
    config: ExecutionConfig,
) -> tuple[dict[str, object], FlowRunResult]:
    stored_trace = store.load_trace(run_id, tenant_id=tenant_id)
    _ = store.load_dataset_descriptor(run_id, tenant_id=tenant_id)
    _ = store.load_replay_envelope(run_id, tenant_id=tenant_id)
    result = execute_flow(resolved_flow=resolved_flow, config=config)
    diff = semantic_trace_diff(stored_trace, result.trace)
    validate_replay(
        stored_trace,
        resolved_flow.plan,
        artifacts=result.artifacts,
        evidence=result.evidence,
        verification_policy=config.verification_policy,
    )
    return diff, result


__all__ = ["replay_with_store"]
