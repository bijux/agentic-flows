# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import dataclasses

import pytest

from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.ids import (
    AgentID,
    EnvironmentFingerprint,
    FlowID,
    InputsFingerprint,
    ResolverID,
    VersionID,
)
from agentic_flows.spec.ontology import StepType
from agentic_flows.spec.resolved_step import ResolvedStep

pytestmark = pytest.mark.unit


def _make_step(index: int) -> ResolvedStep:
    return ResolvedStep(
        spec_version="v1",
        step_index=index,
        step_type=StepType.AGENT,
        agent_id=AgentID(f"agent-{index}"),
        inputs_fingerprint=InputsFingerprint(f"inputs-{index}"),
        declared_dependencies=(),
        expected_artifacts=(),
        agent_invocation=AgentInvocation(
            spec_version="v1",
            agent_id=AgentID(f"agent-{index}"),
            agent_version=VersionID("0.0.0"),
            inputs_fingerprint=InputsFingerprint(f"inputs-{index}"),
            declared_outputs=(),
            execution_mode="seeded",
        ),
        retrieval_request=None,
    )


def test_plan_is_structurally_immutable(plan_hash_for) -> None:
    step = _make_step(0)
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-immutable"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=plan_hash_for("flow-immutable", (step,), {}),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    assert isinstance(plan.steps, tuple)
    assert isinstance(plan.steps[0].declared_dependencies, tuple)

    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.steps = ()

    with pytest.raises(AttributeError):
        plan.steps.append(step)

    with pytest.raises(AttributeError):
        plan.steps[0].declared_dependencies.append(AgentID("agent-x"))
