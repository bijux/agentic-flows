# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import bijux_rar
import pytest

from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    BundleID,
    ClaimID,
    ContractID,
    FlowID,
    GateID,
    InputsFingerprint,
    StepID,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import ArtifactType, EventType, StepType
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.reasoning_claim import ReasoningClaim
from agentic_flows.spec.model.reasoning_step import ReasoningStep
from agentic_flows.spec.model.resolved_step import ResolvedStep

pytestmark = pytest.mark.e2e


def test_verification_failure_halts_flow(
    baseline_policy, resolved_flow_factory
) -> None:
    calls = {"agent": 0}

    def _run(**_kwargs):
        calls["agent"] += 1
        return [
            {
                "artifact_id": "agent-output",
                "artifact_type": ArtifactType.AGENT_INVOCATION.value,
                "content": "payload",
                "parent_artifacts": [],
            }
        ]

    bijux_agent.run = _run

    bijux_rar.reason = lambda **_kwargs: ReasoningBundle(
        spec_version="v1",
        bundle_id=BundleID("bundle-1"),
        claims=(
            ReasoningClaim(
                spec_version="v1",
                claim_id=ClaimID("claim-1"),
                statement="statement",
                confidence=0.5,
                supported_by=(),
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
        evidence_ids=(),
        producer_agent_id=AgentID("agent-a"),
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
        retrieval_request=None,
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
        retrieval_request=None,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-verify"),
        agents=(AgentID("agent-a"), AgentID("agent-b")),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )

    resolved_flow = resolved_flow_factory(manifest, (step_one, step_two))

    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    trace = result.trace

    assert calls["agent"] == 1
    assert trace.events[-1].event_type == EventType.VERIFICATION_FAIL
