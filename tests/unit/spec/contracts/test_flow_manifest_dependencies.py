# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.ontology.ids import AgentID, FlowID
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
)
from agentic_flows.spec.contracts.flow_contract import validate

pytestmark = pytest.mark.unit


def test_ambiguous_dependencies_raise() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-ambiguous"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.SEEDED_RNG,),
            max_magnitude=EntropyMagnitude.LOW,
        ),
        agents=(AgentID("agent-a"), AgentID("agent-b")),
        dependencies=("agent-a",),
        retrieval_contracts=(),
        verification_gates=(),
    )

    with pytest.raises(ValueError, match="dependencies must use"):
        validate(manifest)
