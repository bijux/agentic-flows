# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import pytest

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
    ResolverID,
    VersionID,
)
from agentic_flows.spec.ontology import StepType
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.testing import plan_hash_for, resolved_flow_for


def test_verification_policy_required_before_execution() -> None:
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
        retrieval_request=None,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-policy"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-policy"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint(
            compute_environment_fingerprint()
        ),
        plan_hash=plan_hash_for("flow-policy", (step,), {}),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    with pytest.raises(
        ValueError, match="verification_policy is required before execution"
    ):
        run_flow(
            resolved_flow=resolved_flow_for(manifest, plan),
            mode=RunMode.LIVE,
        )
