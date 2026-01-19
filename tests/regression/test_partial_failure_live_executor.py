# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import pytest

from agentic_flows.runtime.orchestration.determinism_guard import validate_replay
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    FlowID,
    GateID,
    InputsFingerprint,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    ArtifactType,
    DeterminismLevel,
    EventType,
    ReplayAcceptability,
    StepType,
)

pytestmark = pytest.mark.regression


def test_forced_partial_failure_records_incomplete_trace(
    baseline_policy, resolved_flow_factory, entropy_budget
) -> None:
    bijux_agent.run = lambda **_kwargs: [
        {
            "artifact_id": "agent-output",
            "artifact_type": ArtifactType.AGENT_INVOCATION.value,
            "content": "payload",
            "parent_artifacts": [],
        }
    ]

    step = ResolvedStep(
        spec_version="v1",
        step_index=0,
        step_type=StepType.AGENT,
        determinism_level=DeterminismLevel.STRICT,
        agent_id=AgentID("force-partial-failure"),
        inputs_fingerprint=InputsFingerprint("inputs"),
        declared_dependencies=(),
        expected_artifacts=(),
        agent_invocation=AgentInvocation(
            spec_version="v1",
            agent_id=AgentID("force-partial-failure"),
            agent_version=VersionID("0.0.0"),
            inputs_fingerprint=InputsFingerprint("inputs"),
            declared_outputs=(),
            execution_mode="seeded",
        ),
        retrieval_request=None,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-partial"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        agents=(AgentID("force-partial-failure"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, (step,))

    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    trace = result.trace

    assert any(
        event.event_type == EventType.TOOL_CALL_END for event in trace.events
    )
    assert all(
        event.event_type != EventType.REASONING_START for event in trace.events
    )
    assert trace.events[-1].event_type == EventType.STEP_FAILED
    assert result.verification_results[0].reason == "forced_partial_failure"

    with pytest.raises(ValueError, match="failed_steps"):
        validate_replay(
            trace,
            result.resolved_flow.plan,
            verification_policy=baseline_policy,
        )
