# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.planner import ExecutionPlanner
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology.ids import AgentID, DatasetID, FlowID
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
)

pytestmark = pytest.mark.unit


def test_resolver_uses_lexical_tiebreak_for_ordering() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-ordering"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.SEEDED_RNG, EntropySource.DATA),
            max_magnitude=EntropyMagnitude.LOW,
        ),
        replay_envelope=ReplayEnvelope(
            spec_version="v1",
            min_claim_overlap=1.0,
            max_contradiction_delta=0,
            require_same_arbitration=True,
        ),
        dataset=DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID("dataset-order"),
            dataset_version="1.0.0",
            dataset_hash="hash-order",
        ),
        agents=(AgentID("bravo"), AgentID("alpha")),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    resolved = ExecutionPlanner().resolve(manifest)
    ordered = [step.agent_id for step in resolved.plan.steps]

    assert ordered == [AgentID("alpha"), AgentID("bravo")]
