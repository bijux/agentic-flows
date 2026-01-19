# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.observability.trace_diff import semantic_trace_diff
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ids import (
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

pytestmark = pytest.mark.regression


def test_probabilistic_replay_accepts_reordered_events() -> None:
    event_one = ExecutionEvent(
        spec_version="v1",
        event_index=0,
        step_index=0,
        event_type=EventType.STEP_START,
        timestamp_utc="1970-01-01T00:00:00Z",
        payload={"event_type": EventType.STEP_START.value},
        payload_hash="hash-a",
    )
    event_two = ExecutionEvent(
        spec_version="v1",
        event_index=1,
        step_index=1,
        event_type=EventType.STEP_START,
        timestamp_utc="1970-01-01T00:00:01Z",
        payload={"event_type": EventType.STEP_START.value},
        payload_hash="hash-b",
    )

    trace_one = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-prob"),
        parent_flow_id=None,
        child_flow_ids=(),
        determinism_level=DeterminismLevel.PROBABILISTIC,
        replay_acceptability=ReplayAcceptability.STATISTICALLY_BOUNDED,
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(event_one, event_two),
        tool_invocations=(),
        entropy_usage=(),
        finalized=True,
    )
    trace_two = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-prob"),
        parent_flow_id=None,
        child_flow_ids=(),
        determinism_level=DeterminismLevel.PROBABILISTIC,
        replay_acceptability=ReplayAcceptability.STATISTICALLY_BOUNDED,
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(event_two, event_one),
        tool_invocations=(),
        entropy_usage=(),
        finalized=True,
    )

    diff_prob = semantic_trace_diff(
        trace_one,
        trace_two,
        acceptability=ReplayAcceptability.STATISTICALLY_BOUNDED,
    )
    assert diff_prob == {
        "acceptable_events": "different but acceptable under policy"
    }

    diff_strict = semantic_trace_diff(
        trace_one,
        trace_two,
        acceptability=ReplayAcceptability.EXACT_MATCH,
    )
    assert "events" in diff_strict
