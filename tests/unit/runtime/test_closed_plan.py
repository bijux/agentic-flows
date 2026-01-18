# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.resolver import FlowResolver
from agentic_flows.runtime.orchestration.run_flow import RunMode, run_flow
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.resolved_flow import ResolvedFlow
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)

pytestmark = pytest.mark.unit


def test_run_flow_uses_resolved_flow_without_recomputation(monkeypatch) -> None:
    plan = ExecutionPlan(
        spec_version="v1",
        flow_id=FlowID("flow-closed"),
        steps=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("sentinel"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    resolved_flow = ResolvedFlow(
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

    monkeypatch.setattr(FlowResolver, "resolve", _fail_resolve)

    result = run_flow(resolved_flow=resolved_flow, mode=RunMode.PLAN)

    assert result.resolved_flow.plan.plan_hash == PlanHash("sentinel")
