# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.observability.trace_diff import semantic_trace_diff
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import EventType


def test_semantic_trace_diff_ignores_timestamps() -> None:
    event_payload = {"event_type": EventType.STEP_START.value}
    event_one = ExecutionEvent(
        spec_version="v1",
        event_index=0,
        step_index=0,
        event_type=EventType.STEP_START,
        timestamp_utc="1970-01-01T00:00:00Z",
        payload=event_payload,
        payload_hash="hash",
    )
    event_two = ExecutionEvent(
        spec_version="v1",
        event_index=0,
        step_index=0,
        event_type=EventType.STEP_START,
        timestamp_utc="1970-01-01T00:01:00Z",
        payload=event_payload,
        payload_hash="hash",
    )
    trace_one = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-a"),
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(event_one,),
        tool_invocations=(),
        finalized=True,
    )
    trace_two = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-a"),
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(event_two,),
        tool_invocations=(),
        finalized=True,
    )
    assert semantic_trace_diff(trace_one, trace_two) == {}
