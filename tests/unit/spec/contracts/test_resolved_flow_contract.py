# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    EnvironmentFingerprint,
    FlowID,
    InputsFingerprint,
    PlanHash,
    ResolverID,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
    StepType,
)
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.contracts.flow_contract import (
    validate as validate_flow_manifest,
)
from agentic_flows.spec.contracts.execution_plan_contract import (
    validate as validate_execution_plan,
)

pytestmark = pytest.mark.unit


def test_semantic_gate_rejects_invalid_dag() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-invalid-dag"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.SEEDED_RNG,),
            max_magnitude=EntropyMagnitude.LOW,
        ),
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
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.SEEDED_RNG,),
            max_magnitude=EntropyMagnitude.LOW,
        ),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
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
        retrieval_request=None,
    )
    plan = ExecutionSteps(
        spec_version="v1",
        flow_id=FlowID("flow-minimal"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=manifest.entropy_budget,
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    resolved = ExecutionPlan(spec_version="v1", manifest=manifest, plan=plan)

    validate_flow_manifest(manifest)
    validate_execution_plan(resolved)
