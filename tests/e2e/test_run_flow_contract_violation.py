# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import bijux_rag
import bijux_vex
import pytest

from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.model.retrieval_request import RetrievalRequest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    FlowID,
    GateID,
    InputsFingerprint,
    RequestID,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EventType,
    EvidenceDeterminism,
    ReplayAcceptability,
    StepType,
)

pytestmark = pytest.mark.e2e


def test_contract_violation_aborts(
    baseline_policy,
    resolved_flow_factory,
    entropy_budget,
    replay_envelope,
    dataset_descriptor,
) -> None:
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
            "determinism": EvidenceDeterminism.DETERMINISTIC.value,
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
        determinism_level=DeterminismLevel.STRICT,
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
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        replay_envelope=replay_envelope,
        dataset=dataset_descriptor,
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-expected"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, (step,))

    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    trace = result.trace

    assert not called["agent"]
    assert result.artifacts == []
    assert result.evidence == []
    assert trace.events[-1].event_type == EventType.RETRIEVAL_FAILED
