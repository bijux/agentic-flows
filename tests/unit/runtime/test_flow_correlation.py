# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.observability.flow_correlation import (
    validate_flow_correlation,
)
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)


def test_flow_correlation_requires_parent() -> None:
    parent = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("parent"),
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        finalized=True,
    )
    child = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("child"),
        parent_flow_id=FlowID("parent"),
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        finalized=True,
    )
    validate_flow_correlation(child, [parent])


def test_flow_correlation_rejects_missing_parent() -> None:
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("child"),
        parent_flow_id=FlowID("parent"),
        child_flow_ids=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        finalized=True,
    )
    with pytest.raises(ValueError, match="parent_flow_id"):
        validate_flow_correlation(trace, [])
