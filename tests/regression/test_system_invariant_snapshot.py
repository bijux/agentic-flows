# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows import api
from agentic_flows.core import authority
from agentic_flows.spec.contracts import compatibility_contract
from agentic_flows.spec.ontology.ontology import (
    ArtifactScope,
    ArbitrationRule,
    StepType,
    VerificationPhase,
)

pytestmark = pytest.mark.regression


def test_system_invariant_snapshot() -> None:
    assert set(api.__all__) == {
        "ArbitrationPolicy",
        "ExecutionConfig",
        "ExecutionPlan",
        "FlowManifest",
        "FlowRunResult",
        "RunMode",
        "VerificationPolicy",
        "execute_flow",
    }
    assert [scope.value for scope in ArtifactScope] == [
        "ephemeral",
        "working",
        "audit",
    ]
    assert [step.value for step in StepType] == [
        "agent",
        "retrieval",
        "reasoning",
        "verification",
    ]
    assert [phase.value for phase in VerificationPhase] == [
        "pre_execution",
        "post_execution",
    ]
    assert [rule.value for rule in ArbitrationRule] == [
        "unanimous",
        "quorum",
        "strict_first_failure",
    ]
    assert callable(authority.enforce_runtime_semantics)
    assert compatibility_contract.breaks_replay("plan_hash") is True
    assert compatibility_contract.allowed_to_evolve("doc_text") is True
