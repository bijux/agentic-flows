# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.runtime.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.environment import compute_environment_fingerprint
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
from agentic_flows.spec.resolved_step import ResolvedStep


def test_execution_order_mismatch_rejected() -> None:
    step_one = ResolvedStep(
        spec_version="v1",
        step_index=1,
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
        step_index=0,
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
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-order"),
        steps=(step_one, step_two),
        environment_fingerprint=EnvironmentFingerprint(compute_environment_fingerprint()),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    with pytest.raises(ValueError, match="execution order must match resolver step order"):
        DryRunExecutor().execute(plan)
