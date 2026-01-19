# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.core.authority import enforce_runtime_semantics, finalize_trace
from agentic_flows.core.errors import SemanticViolationError
from agentic_flows.runtime.observability.trace_recorder import TraceRecorder
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import EventType

pytestmark = pytest.mark.unit


def test_finalize_trace_twice_rejected() -> None:
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow"),
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        finalized=False,
    )

    finalize_trace(trace)
    with pytest.raises(SemanticViolationError):
        finalize_trace(trace)


def test_emit_event_without_authority_fails() -> None:
    recorder = TraceRecorder()
    event = ExecutionEvent(
        spec_version="v1",
        event_index=0,
        step_index=0,
        event_type=EventType.STEP_START,
        timestamp_utc="1970-01-01T00:00:00Z",
        payload={"event_type": EventType.STEP_START.value},
        payload_hash="payload",
    )
    with pytest.raises(TypeError):
        recorder.record(event, authority=None)  # type: ignore[arg-type]


def test_bypass_verification_is_rejected() -> None:
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow"),
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        finalized=True,
    )

    class _Result:
        def __init__(self) -> None:
            self.trace = trace
            self.verification_results = ()
            self.verification_arbitrations = ()
            self.reasoning_bundles = (object(),)

    with pytest.raises(SemanticViolationError):
        enforce_runtime_semantics(_Result(), mode="live")
