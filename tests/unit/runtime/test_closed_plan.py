# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.planner import ExecutionPlanner
from agentic_flows.runtime.orchestration.execute_flow import RunMode, execute_flow
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)

pytestmark = pytest.mark.unit


def test_run_flow_uses_resolved_flow_without_recomputation(monkeypatch) -> None:
    plan = ExecutionSteps(
        spec_version="v1",
        flow_id=FlowID("flow-closed"),
        steps=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("sentinel"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    resolved_flow = ExecutionPlan(
        spec_version="v1",
        manifest=FlowManifest(
            spec_version="v1",
            flow_id=FlowID("flow-closed"),
            agents=(),
            dependencies=(),
            retrieval_contracts=(),
            verification_gates=(),
        ),
        plan=plan,
    )

    def _fail_resolve(*_args, **_kwargs):
        raise AssertionError(
            "resolver must not be called when resolved_flow is provided"
        )

    monkeypatch.setattr(ExecutionPlanner, "resolve", _fail_resolve)

    result = execute_flow(resolved_flow=resolved_flow, mode=RunMode.PLAN)

    assert result.resolved_flow.plan.plan_hash == PlanHash("sentinel")
