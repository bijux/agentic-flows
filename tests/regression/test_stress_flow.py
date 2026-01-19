# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import bijux_rag
import bijux_rar
import bijux_vex
import pytest
from tests.helpers import build_claim_statement

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

pytestmark = pytest.mark.regression


def test_real_world_stress_flow(
    baseline_policy,
    resolved_flow_factory,
    entropy_budget,
    replay_envelope,
    dataset_descriptor,
) -> None:
    counter = {"value": 0}

    def _run(**_kwargs):
        counter["value"] += 1
        return [
            {
                "artifact_id": f"agent-output-{counter['value']}",
                "artifact_type": ArtifactType.AGENT_INVOCATION.value,
                "content": "payload",
                "parent_artifacts": [],
            }
        ]

    bijux_agent.run = _run
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

    statements = []

    def _reason(agent_outputs, evidence, seed):
        base_statement = build_claim_statement(agent_outputs, evidence)
        statement = base_statement if not statements else f"not {base_statement}"
        statements.append(statement)
        return ReasoningBundle(
            spec_version="v1",
            bundle_id=BundleID(f"bundle-{len(statements)}"),
            claims=(
                ReasoningClaim(
                    spec_version="v1",
                    claim_id=ClaimID(f"claim-{len(statements)}"),
                    statement=statement,
                    confidence=0.6,
                    supported_by=(EvidenceID("ev-1"),),
                ),
            ),
            steps=(
                ReasoningStep(
                    spec_version="v1",
                    step_id=StepID(f"step-{len(statements)}"),
                    input_claims=(),
                    output_claims=(ClaimID(f"claim-{len(statements)}"),),
                    method="aggregation",
                ),
            ),
            evidence_ids=(EvidenceID("ev-1"),),
            producer_agent_id=AgentID("agent-a"),
        )

    bijux_rar.reason = _reason

    request = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-1"),
        query="query",
        vector_contract_id=ContractID("contract-1"),
        top_k=1,
        scope="project",
    )
    steps = (
        ResolvedStep(
            spec_version="v1",
            step_index=0,
            step_type=StepType.AGENT,
            determinism_level=DeterminismLevel.STRICT,
            agent_id=AgentID("agent-a"),
            inputs_fingerprint=InputsFingerprint("inputs-a"),
            declared_dependencies=(),
            expected_artifacts=(),
            agent_invocation=AgentInvocation(
                spec_version="v1",
                agent_id=AgentID("agent-a"),
                agent_version=VersionID("0.0.0"),
                inputs_fingerprint=InputsFingerprint("inputs-a"),
                declared_outputs=(),
                execution_mode="seeded",
            ),
            retrieval_request=request,
        ),
        ResolvedStep(
            spec_version="v1",
            step_index=1,
            step_type=StepType.AGENT,
            determinism_level=DeterminismLevel.STRICT,
            agent_id=AgentID("agent-a"),
            inputs_fingerprint=InputsFingerprint("inputs-b"),
            declared_dependencies=(),
            expected_artifacts=(),
            agent_invocation=AgentInvocation(
                spec_version="v1",
                agent_id=AgentID("agent-a"),
                agent_version=VersionID("0.0.0"),
                inputs_fingerprint=InputsFingerprint("inputs-b"),
                declared_outputs=(),
                execution_mode="seeded",
            ),
            retrieval_request=request,
        ),
        ResolvedStep(
            spec_version="v1",
            step_index=2,
            step_type=StepType.AGENT,
            determinism_level=DeterminismLevel.STRICT,
            agent_id=AgentID("force-partial-failure"),
            inputs_fingerprint=InputsFingerprint("inputs-c"),
            declared_dependencies=(),
            expected_artifacts=(),
            agent_invocation=AgentInvocation(
                spec_version="v1",
                agent_id=AgentID("force-partial-failure"),
                agent_version=VersionID("0.0.0"),
                inputs_fingerprint=InputsFingerprint("inputs-c"),
                declared_outputs=(),
                execution_mode="seeded",
            ),
            retrieval_request=request,
        ),
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-stress"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        replay_envelope=replay_envelope,
        dataset=dataset_descriptor,
        agents=(AgentID("agent-a"), AgentID("force-partial-failure")),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-1"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, steps)

    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )

    assert any(
        event.event_type == EventType.RETRIEVAL_START for event in result.trace.events
    )
    assert any(
        event.event_type == EventType.REASONING_START for event in result.trace.events
    )
    assert any(
        event.event_type == EventType.STEP_FAILED for event in result.trace.events
    )
    assert any(
        arbitration.decision == "FAIL"
        for arbitration in result.verification_arbitrations
    )
    assert any(
        outcome.engine_id == "contradiction" and outcome.status == "FAIL"
        for outcome in result.verification_results
    )
