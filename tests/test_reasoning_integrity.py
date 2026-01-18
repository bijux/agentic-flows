# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import bijux_agent
import bijux_rar

from agentic_flows.runtime.live_executor import LiveExecutor
from agentic_flows.runtime.environment import compute_environment_fingerprint
from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.ids import (
    AgentID,
    BundleID,
    ClaimID,
    EnvironmentFingerprint,
    EvidenceID,
    FlowID,
    InputsFingerprint,
    ResolverID,
    StepID,
    VersionID,
)


def test_reasoning_references_missing_evidence() -> None:
    bijux_agent.run = lambda **_kwargs: [
        {
            "artifact_id": "agent-output",
            "artifact_type": "agent_invocation",
            "content": "payload",
            "parent_artifacts": [],
        }
    ]

    def _bad_reason(**_kwargs):
        return ReasoningBundle(
            spec_version="v1",
            bundle_id=BundleID("bundle-1"),
            claims=(
                ReasoningClaim(
                    spec_version="v1",
                    claim_id=ClaimID("claim-1"),
                    statement="statement",
                    confidence=0.5,
                    supported_by=(EvidenceID("missing-evidence"),),
                ),
            ),
            steps=(
                ReasoningStep(
                    spec_version="v1",
                    step_id=StepID("step-1"),
                    input_claims=(),
                    output_claims=(ClaimID("claim-1"),),
                    method="deduction",
                ),
            ),
            evidence_ids=(EvidenceID("missing-evidence"),),
            producer_agent_id=AgentID("agent-a"),
        )

    bijux_rar.reason = _bad_reason

    step = ResolvedStep(
        spec_version="v1",
        step_index=0,
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
        retrieval_request=None,
    )
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-reasoning"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint(compute_environment_fingerprint()),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    trace, artifacts, evidence, _, _ = LiveExecutor().execute(plan)

    assert evidence == []
    assert trace.events[-1].event_type == "REASONING_FAILED"
