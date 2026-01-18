# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import dataclasses

import pytest

from agentic_flows.runtime.trace_recorder import AppendOnlyList
from agentic_flows.spec.execution_event import ExecutionEvent
from agentic_flows.spec.execution_trace import ExecutionTrace
from agentic_flows.spec.ids import EnvironmentFingerprint, FlowID, PlanHash, ResolverID
from agentic_flows.spec.ontology import EventType


def test_trace_is_immutable() -> None:
    events = AppendOnlyList()
    events.append(
        ExecutionEvent(
            spec_version="v1",
            event_index=0,
            step_index=0,
            event_type=EventType.STEP_START,
            timestamp_utc="1970-01-01T00:00:00Z",
            payload_hash="x",
        )
    )
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-trace"),
        environment_fingerprint=EnvironmentFingerprint("env-fingerprint"),
        plan_hash=PlanHash("plan-hash"),
        resolver_id=ResolverID("agentic-flows:v0"),
        events=tuple(events),
        finalized=False,
    )
    trace.finalize()

    with pytest.raises(dataclasses.FrozenInstanceError):
        trace.flow_id = "mutated"

    with pytest.raises(TypeError):
        trace.events[0] = ExecutionEvent(
            spec_version="v1",
            event_index=999,
            step_index=0,
            event_type=EventType.STEP_START,
            timestamp_utc="1970-01-01T00:00:00Z",
            payload_hash="x",
        )

    with pytest.raises(AttributeError):
        trace.events.pop()

    original_first = trace.events[0]
    with pytest.raises(AttributeError):
        trace.events.append(
            ExecutionEvent(
                spec_version="v1",
                event_index=999,
                step_index=0,
                event_type=EventType.STEP_END,
                timestamp_utc="1970-01-01T00:00:01Z",
                payload_hash="y",
            )
        )
    assert trace.events[0] == original_first
