# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

from dataclasses import asdict
import json

import bijux_agent
import bijux_rag
import bijux_rar
import bijux_vex

from agentic_flows.runtime.environment import compute_environment_fingerprint
from agentic_flows.runtime.run_flow import RunMode, run_flow
from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import (
    AgentID,
    BundleID,
    ClaimID,
    ContractID,
    EnvironmentFingerprint,
    FlowID,
    GateID,
    InputsFingerprint,
    RequestID,
    ResolverID,
    StepID,
    VersionID,
)
from agentic_flows.spec.ontology import ArtifactType, StepType
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.retrieval_request import RetrievalRequest
from agentic_flows.testing import baseline_policy, plan_hash_for, resolved_flow_for


def test_reasoning_determinism() -> None:
    def _deterministic_reason(agent_outputs, evidence, seed):
        return ReasoningBundle(
            spec_version="v1",
            bundle_id=BundleID(f"bundle-{seed}"),
            claims=(
                ReasoningClaim(
                    spec_version="v1",
                    claim_id=ClaimID("claim-1"),
                    statement="statement",
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

    bijux_rar.reason = _deterministic_reason

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
            "source_uri": "file://doc-1",
            "content": "content",
            "score": 0.9,
            "vector_contract_id": "contract-1",
        }
    ]
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: True

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
        flow_id=FlowID("flow-reasoning"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-1"),),
        verification_gates=(GateID("gate-a"),),
    )
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-reasoning"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint(
            compute_environment_fingerprint()
        ),
        plan_hash=plan_hash_for("flow-reasoning", (step,), {}),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    result_one = run_flow(
        resolved_flow=resolved_flow_for(manifest, plan),
        mode=RunMode.LIVE,
        verification_policy=baseline_policy(),
    )
    result_two = run_flow(
        resolved_flow=resolved_flow_for(manifest, plan),
        mode=RunMode.LIVE,
        verification_policy=baseline_policy(),
    )

    bundle_one = result_one.reasoning_bundles[0]
    bundle_two = result_two.reasoning_bundles[0]

    payload_one = json.dumps(asdict(bundle_one), sort_keys=True)
    payload_two = json.dumps(asdict(bundle_two), sort_keys=True)

    assert payload_one == payload_two
