# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import bijux_agent
import bijux_rag
import bijux_vex

from agentic_flows.runtime.environment import compute_environment_fingerprint
from agentic_flows.runtime.run_flow import RunMode, run_flow
from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import (
    AgentID,
    ContractID,
    EnvironmentFingerprint,
    FlowID,
    GateID,
    InputsFingerprint,
    RequestID,
    ResolverID,
    VersionID,
)
from agentic_flows.spec.ontology import EventType, StepType
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.retrieval_request import RetrievalRequest
from agentic_flows.testing import baseline_policy, plan_hash_for, resolved_flow_for


def test_contract_violation_aborts() -> None:
    request = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-violate"),
        query="test",
        vector_contract_id=ContractID("contract-expected"),
        top_k=1,
        scope="project",
    )

    bijux_rag.retrieve = lambda **_kwargs: [
        {
            "evidence_id": "ev-bad",
            "source_uri": "file://bad",
            "content": "bad",
            "score": 0.1,
            "vector_contract_id": "contract-other",
        }
    ]
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: False

    called = {"agent": False}

    def _run(**_kwargs):
        called["agent"] = True
        return []

    bijux_agent.run = _run

    step = ResolvedStep(
        spec_version="v1",
        step_index=0,
        step_type=StepType.AGENT,
        agent_id=AgentID("agent-a"),
        inputs_fingerprint=InputsFingerprint("inputs"),
        declared_dependencies=(),
        expected_artifacts=(),
        agent_invocation=AgentInvocation(
            spec_version="v1",
            agent_id=AgentID("agent-a"),
            agent_version=VersionID("0.0.0"),
            inputs_fingerprint=InputsFingerprint("inputs"),
            declared_outputs=(),
            execution_mode="seeded",
        ),
        retrieval_request=request,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-violation"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-expected"),),
        verification_gates=(GateID("gate-a"),),
    )
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-violation"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint(
            compute_environment_fingerprint()
        ),
        plan_hash=plan_hash_for("flow-violation", (step,), {}),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    result = run_flow(
        resolved_flow=resolved_flow_for(manifest, plan),
        mode=RunMode.LIVE,
        verification_policy=baseline_policy(),
    )
    trace = result.trace

    assert not called["agent"]
    assert result.artifacts == []
    assert result.evidence == []
    assert trace.events[-1].event_type == EventType.RETRIEVAL_FAILED
