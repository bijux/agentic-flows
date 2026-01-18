# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.determinism_guard import validate_replay
from agentic_flows.runtime.orchestration.run_flow import RunMode, run_flow
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    FlowID,
    GateID,
    ResolverID,
)

pytestmark = pytest.mark.regression


def test_replay_equivalence(deterministic_environment) -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-replay"),
        agents=(AgentID("alpha"), AgentID("bravo")),
        dependencies=("bravo:alpha",),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )

    result = run_flow(manifest, mode=RunMode.PLAN)
    plan = result.resolved_flow.plan
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=plan.flow_id,
        environment_fingerprint=plan.environment_fingerprint,
        plan_hash=plan.plan_hash,
        resolver_id=ResolverID("agentic-flows:v0"),
        events=(),
        tool_invocations=(),
        finalized=False,
    )
    trace.finalize()

    validate_replay(trace, plan)
