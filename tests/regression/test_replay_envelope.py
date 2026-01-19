# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.observability.trace_diff import semantic_trace_diff
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology.ids import (
    ClaimID,
    DatasetID,
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    ReplayAcceptability,
)

pytestmark = pytest.mark.regression


def test_statistical_envelope_rejects_low_claim_overlap() -> None:
    envelope = ReplayEnvelope(
        spec_version="v1",
        min_claim_overlap=0.8,
        max_contradiction_delta=0,
        require_same_arbitration=True,
    )
    dataset = DatasetDescriptor(
        spec_version="v1",
        dataset_id=DatasetID("dataset-envelope"),
        dataset_version="1.0.0",
        dataset_hash="hash-envelope",
    )
    expected = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow"),
        parent_flow_id=None,
        child_flow_ids=(),
        determinism_level=DeterminismLevel.PROBABILISTIC,
        replay_acceptability=ReplayAcceptability.STATISTICALLY_BOUNDED,
        dataset=dataset,
        replay_envelope=envelope,
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        entropy_usage=(),
        claim_ids=(ClaimID("c1"), ClaimID("c2"), ClaimID("c3")),
        contradiction_count=0,
        arbitration_decision="pass",
        finalized=True,
    )
    observed = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow"),
        parent_flow_id=None,
        child_flow_ids=(),
        determinism_level=DeterminismLevel.PROBABILISTIC,
        replay_acceptability=ReplayAcceptability.STATISTICALLY_BOUNDED,
        dataset=dataset,
        replay_envelope=envelope,
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("resolver"),
        events=(),
        tool_invocations=(),
        entropy_usage=(),
        claim_ids=(ClaimID("c1"),),
        contradiction_count=0,
        arbitration_decision="pass",
        finalized=True,
    )
    diff = semantic_trace_diff(
        expected,
        observed,
        acceptability=ReplayAcceptability.STATISTICALLY_BOUNDED,
    )
    assert "claim_overlap" in diff
    assert "non_determinism_report" in diff
