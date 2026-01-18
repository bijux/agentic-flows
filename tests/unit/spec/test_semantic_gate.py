# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import (
    AgentID,
    EnvironmentFingerprint,
    FlowID,
    InputsFingerprint,
    PlanHash,
    ResolverID,
    VersionID,
)
from agentic_flows.spec.ontology import StepType
from agentic_flows.spec.resolved_flow import ResolvedFlow
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.semantic_validation import (
    validate_flow_manifest,
    validate_resolved_flow,
)

pytestmark = pytest.mark.unit


def test_semantic_gate_rejects_invalid_dag() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-invalid-dag"),
        agents=(AgentID("agent-a"), AgentID("agent-b")),
        dependencies=("agent-a:agent-b", "agent-b:agent-a"),
        retrieval_contracts=(),
        verification_gates=(),
    )

    with pytest.raises(ValueError, match="dependencies must form a reachable DAG"):
        validate_flow_manifest(manifest)


def test_semantic_gate_accepts_minimal_valid_flow() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-minimal"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
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
        retrieval_request=None,
    )
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-minimal"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    resolved = ResolvedFlow(spec_version="v1", manifest=manifest, plan=plan)

    validate_flow_manifest(manifest)
    validate_resolved_flow(resolved)
