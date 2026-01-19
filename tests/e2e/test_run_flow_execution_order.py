# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

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
    ContractID,
    FlowID,
    GateID,
    InputsFingerprint,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    ReplayAcceptability,
    StepType,
)
from agentic_flows.spec.model.resolved_step import ResolvedStep

pytestmark = pytest.mark.e2e


def test_execution_order_mismatch_rejected(
    baseline_policy, resolved_flow_factory, deterministic_environment, entropy_budget
) -> None:
    step_one = ResolvedStep(
        spec_version="v1",
        step_index=1,
        step_type=StepType.AGENT,
        determinism_level=DeterminismLevel.STRICT,
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
        step_type=StepType.AGENT,
        determinism_level=DeterminismLevel.STRICT,
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
        flow_id=FlowID("flow-order"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        agents=(AgentID("agent-a"), AgentID("agent-b")),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(
        manifest,
        (step_one, step_two),
        environment_fingerprint=deterministic_environment,
    )

    with pytest.raises(
        ValueError, match="execution order must match resolver step order"
    ):
        execute_flow(
            resolved_flow=resolved_flow,
            config=ExecutionConfig(
                mode=RunMode.DRY_RUN, verification_policy=baseline_policy
            ),
        )
