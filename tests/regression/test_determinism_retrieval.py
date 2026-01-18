# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import bijux_rag
import bijux_rar
import bijux_vex
import pytest

from agentic_flows.runtime.orchestration.execute_flow import RunMode, execute_flow
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.flow_manifest import FlowManifest
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
from agentic_flows.spec.ontology.ontology import ArtifactType, StepType
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.reasoning_claim import ReasoningClaim
from agentic_flows.spec.model.reasoning_step import ReasoningStep
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.model.retrieval_request import RetrievalRequest

pytestmark = pytest.mark.regression


def test_retrieval_determinism(baseline_policy, resolved_flow_factory) -> None:
    request = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-1"),
        query="what is bijux",
        vector_contract_id=ContractID("contract-1"),
        top_k=2,
        scope="project",
    )

    def _deterministic_retrieve(**_kwargs):
        return [
            {
                "evidence_id": "ev-1",
                "source_uri": "file://doc-1",
                "content": "alpha",
                "score": 0.9,
                "vector_contract_id": "contract-1",
            },
            {
                "evidence_id": "ev-2",
                "source_uri": "file://doc-2",
                "content": "beta",
                "score": 0.8,
                "vector_contract_id": "contract-1",
            },
        ]

    bijux_rag.retrieve = _deterministic_retrieve
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: True

    bijux_agent.run = lambda **_kwargs: [
        {
            "artifact_id": "agent-output",
            "artifact_type": ArtifactType.AGENT_INVOCATION.value,
            "content": "payload",
            "parent_artifacts": [],
        }
    ]
    bijux_rar.reason = lambda **_kwargs: ReasoningBundle(
        spec_version="v1",
        bundle_id=BundleID("bundle-1"),
        claims=(
            ReasoningClaim(
                spec_version="v1",
                claim_id=ClaimID("claim-1"),
                statement="statement",
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
        flow_id=FlowID("flow-retrieval"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-1"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, (step,))

    result_one = execute_flow(
        resolved_flow=resolved_flow,
        mode=RunMode.LIVE,
        verification_policy=baseline_policy,
    )
    result_two = execute_flow(
        resolved_flow=resolved_flow,
        mode=RunMode.LIVE,
        verification_policy=baseline_policy,
    )
    evidence_one = result_one.evidence
    evidence_two = result_two.evidence

    assert [(item.evidence_id, item.content_hash) for item in evidence_one] == [
        (item.evidence_id, item.content_hash) for item in evidence_two
    ]
