# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    ReplayAcceptability,
)

pytestmark = pytest.mark.unit


def test_trace_access_before_finalize_raises() -> None:
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-misuse"),
        parent_flow_id=None,
        child_flow_ids=(),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan-hash"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("agentic-flows:v0"),
        events=(),
        tool_invocations=(),
        entropy_usage=(),
        finalized=False,
    )

    with pytest.raises(
        RuntimeError, match="ExecutionTrace accessed before finalization"
    ):
        _ = trace.flow_id
