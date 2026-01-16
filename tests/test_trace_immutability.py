import dataclasses

import pytest

from agentic_flows.runtime import resolver as resolver_module
from agentic_flows.runtime.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.execution_event import ExecutionEvent
from agentic_flows.spec.flow_manifest import FlowManifest


def test_trace_is_immutable() -> None:
    manifest = FlowManifest(
        flow_id="flow-trace",
        agents=("agent-a",),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    resolver_module.compute_environment_fingerprint = lambda: "env-fingerprint"
    resolver = FlowResolver()
    resolver._bijux_agent_version = "0.0.0"
    plan = resolver.resolve(manifest)
    trace = DryRunExecutor().execute(plan)

    with pytest.raises(dataclasses.FrozenInstanceError):
        trace.flow_id = "mutated"

    with pytest.raises(TypeError):
        trace.events[0] = ExecutionEvent(
            event_index=999,
            step_index=0,
            event_type="STEP_START",
            timestamp_utc="1970-01-01T00:00:00Z",
            payload_hash="x",
        )

    with pytest.raises(TypeError):
        trace.events.pop()

    original_first = trace.events[0]
    trace.events.append(
        ExecutionEvent(
            event_index=999,
            step_index=0,
            event_type="STEP_END",
            timestamp_utc="1970-01-01T00:00:01Z",
            payload_hash="y",
        )
    )
    assert trace.events[0] == original_first
