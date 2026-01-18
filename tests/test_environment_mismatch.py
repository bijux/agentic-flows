# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.runtime.dry_run_executor import DryRunExecutor
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


def test_environment_fingerprint_mismatch_blocks_execution() -> None:
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
        flow_id=FlowID("flow-mismatch"),
        steps=(step,),
        environment_fingerprint=EnvironmentFingerprint("mismatch"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )

    with pytest.raises(ValueError, match="environment_fingerprint mismatch"):
        DryRunExecutor().execute(plan)
