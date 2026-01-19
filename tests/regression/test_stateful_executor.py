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
from agentic_flows.spec.ontology.ontology import ArtifactType, StepType
from tests.helpers import build_claim_statement

pytestmark = pytest.mark.regression


def test_stateful_executor_replays_and_dry_run_match(
    baseline_policy, resolved_flow_factory
) -> None:
    bijux_agent.run = lambda agent_id, **_kwargs: [
        {
            "artifact_id": f"agent-output-{agent_id}",
            "artifact_type": ArtifactType.AGENT_INVOCATION.value,
            "content": f"payload-{agent_id}",
            "parent_artifacts": [],
        }
    ]
    bijux_rag.retrieve = lambda **_kwargs: [
        {
            "evidence_id": "ev-1",
            "source_uri": "file://doc",
            "content": "content",
            "score": 0.9,
            "vector_contract_id": "contract-1",
        }
    ]
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: True

    def _reason(agent_outputs, evidence, seed):
        statement = build_claim_statement(agent_outputs, evidence)
        return ReasoningBundle(
            spec_version="v1",
            bundle_id=BundleID(f"bundle-{seed}"),
            claims=(
                ReasoningClaim(
                    spec_version="v1",
                    claim_id=ClaimID("claim-1"),
                    statement=statement,
                    confidence=0.5,
                    supported_by=(evidence[0].evidence_id,),
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
            evidence_ids=(evidence[0].evidence_id,),
            producer_agent_id=AgentID("agent-a"),
        )

    bijux_rar.reason = _reason

    request_one = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-1"),
        query="query",
        vector_contract_id=ContractID("contract-1"),
        top_k=1,
        scope="project",
    )
    request_two = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-2"),
        query="query",
        vector_contract_id=ContractID("contract-1"),
        top_k=1,
        scope="project",
    )
    step_one = ResolvedStep(
        spec_version="v1",
        step_index=0,
        step_type=StepType.AGENT,
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
        retrieval_request=request_one,
    )
    step_two = ResolvedStep(
        spec_version="v1",
        step_index=1,
        step_type=StepType.AGENT,
        agent_id=AgentID("agent-b"),
        inputs_fingerprint=InputsFingerprint("inputs-b"),
        declared_dependencies=(),
        expected_artifacts=(),
        agent_invocation=AgentInvocation(
            spec_version="v1",
            agent_id=AgentID("agent-b"),
            agent_version=VersionID("0.0.0"),
            inputs_fingerprint=InputsFingerprint("inputs-b"),
            declared_outputs=(),
            execution_mode="seeded",
        ),
        retrieval_request=request_two,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-state"),
        agents=(AgentID("agent-a"), AgentID("agent-b")),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-1"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, (step_one, step_two))

    live_one = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    live_two = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    dry_run = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.DRY_RUN),
    )

    def _state_hashes(result):
        return {
            artifact.artifact_id: artifact.content_hash
            for artifact in result.artifacts
            if artifact.artifact_type == ArtifactType.EXECUTOR_STATE
        }

    assert _state_hashes(live_one) == _state_hashes(live_two)
    assert _state_hashes(live_one) == _state_hashes(dry_run)
