# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.run_flow import RunMode, run_flow
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    EnvironmentFingerprint,
    FlowID,
    GateID,
    InputsFingerprint,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import StepType
from agentic_flows.spec.model.resolved_step import ResolvedStep

pytestmark = pytest.mark.e2e


def test_environment_fingerprint_mismatch_blocks_execution(
    baseline_policy, resolved_flow_factory
) -> None:
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
        flow_id=FlowID("flow-mismatch"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(
        manifest,
        (step,),
        environment_fingerprint=EnvironmentFingerprint("mismatch"),
    )

    with pytest.raises(ValueError, match="environment_fingerprint mismatch"):
        run_flow(
            resolved_flow=resolved_flow,
            mode=RunMode.DRY_RUN,
            verification_policy=baseline_policy,
        )
