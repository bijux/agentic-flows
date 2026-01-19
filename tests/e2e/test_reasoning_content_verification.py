# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import bijux_rag
import bijux_rar
import bijux_vex
import pytest

from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.reasoning_claim import ReasoningClaim
from agentic_flows.spec.model.reasoning_step import ReasoningStep
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.model.retrieval_request import RetrievalRequest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    BundleID,
    ClaimID,
    ContractID,
    EvidenceID,
    FlowID,
    GateID,
    InputsFingerprint,
    RequestID,
    StepID,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    ArtifactType,
    DeterminismLevel,
    EventType,
    EvidenceDeterminism,
    ReplayAcceptability,
    StepType,
)

pytestmark = pytest.mark.e2e


def test_reasoning_content_verification_catches_bad_claim(
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
    bijux_rag.retrieve = lambda **_kwargs: [
        {
            "evidence_id": "ev-1",
            "determinism": EvidenceDeterminism.DETERMINISTIC.value,
            "source_uri": "file://doc",
            "content": "content",
            "score": 0.9,
            "vector_contract_id": "contract-1",
        }
    ]
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: True
    bijux_rar.reason = lambda **_kwargs: ReasoningBundle(
        spec_version="v1",
        bundle_id=BundleID("bundle-1"),
        claims=(
            ReasoningClaim(
                spec_version="v1",
                claim_id=ClaimID("claim-1"),
                statement="evidence_id=ev-1 artifact_hash=missing",
                confidence=0.5,
                supported_by=(EvidenceID("ev-1"),),
            ),
        ),
        steps=(
            ReasoningStep(
                spec_version="v1",
                step_id=StepID("step-1"),
                input_claims=(),
                output_claims=(ClaimID("claim-1"),),
                method="aggregation",
            ),
        ),
        evidence_ids=(EvidenceID("ev-1"),),
        producer_agent_id=AgentID("agent-a"),
    )

    request = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-1"),
        query="query",
        vector_contract_id=ContractID("contract-1"),
        top_k=1,
        scope="project",
    )
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
        flow_id=FlowID("flow-bad-claim"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-1"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, (step,))

    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )

    assert any(
        event.event_type == EventType.VERIFICATION_FAIL
        for event in result.trace.events
    )
    assert result.trace.events[-1].event_type in {
        EventType.VERIFICATION_FAIL,
        EventType.VERIFICATION_ARBITRATION,
    }
