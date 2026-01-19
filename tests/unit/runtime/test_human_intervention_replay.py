# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.determinism_guard import validate_replay
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import EventType


def test_human_intervention_event_breaks_replay() -> None:
    plan = ExecutionSteps(
        spec_version="v1",
        flow_id=FlowID("flow"),
        steps=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    event = ExecutionEvent(
        spec_version="v1",
        event_index=0,
        step_index=0,
        event_type=EventType.HUMAN_INTERVENTION,
        timestamp_utc="1970-01-01T00:00:00Z",
        payload={"event_type": EventType.HUMAN_INTERVENTION.value, "justification": "override"},
        payload_hash="override",
    )
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow"),
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("agentic-flows:v0"),
        events=(event,),
        tool_invocations=(),
        finalized=True,
    )
    with pytest.raises(ValueError, match="human_intervention_events"):
        validate_replay(trace, plan)
