# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import dataclasses

import pytest

from agentic_flows.runtime.observability.trace_recorder import AppendOnlyList
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology.ids import (
    DatasetID,
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EventType,
    ReplayAcceptability,
)

pytestmark = pytest.mark.unit


def test_trace_is_immutable() -> None:
    events = AppendOnlyList()
    events.append(
        ExecutionEvent(
            spec_version="v1",
            event_index=0,
            step_index=0,
            event_type=EventType.STEP_START,
            timestamp_utc="1970-01-01T00:00:00Z",
            payload={"event_type": EventType.STEP_START.value},
            payload_hash="x",
        )
    )
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-trace"),
        parent_flow_id=None,
        child_flow_ids=(),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        dataset=DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID("dataset-trace"),
            dataset_version="1.0.0",
            dataset_hash="hash-trace",
        ),
        replay_envelope=ReplayEnvelope(
            spec_version="v1",
            min_claim_overlap=1.0,
            max_contradiction_delta=0,
            require_same_arbitration=True,
        ),
        environment_fingerprint=EnvironmentFingerprint("env-fingerprint"),
        plan_hash=PlanHash("plan-hash"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("agentic-flows:v0"),
        events=tuple(events),
        tool_invocations=(),
        entropy_usage=(),
        claim_ids=(),
        contradiction_count=0,
        arbitration_decision="none",
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
            payload={"event_type": EventType.STEP_START.value},
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
                payload={"event_type": EventType.STEP_END.value},
                payload_hash="y",
            )
        )
    assert trace.events[0] == original_first
