# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.contracts.flow_contract import validate
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import AgentID, ContractID, FlowID, GateID
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
)

pytestmark = pytest.mark.unit


def test_invalid_manifest_rejected() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID(""),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.SEEDED_RNG,),
            max_magnitude=EntropyMagnitude.LOW,
        ),
        agents=(AgentID("agent-a"),),
        dependencies=("dep-a",),
        retrieval_contracts=(ContractID("retrieval-a"),),
        verification_gates=(GateID("gate-a"),),
    )

    with pytest.raises(ValueError, match="flow_id must be a non-empty string"):
        validate(manifest)
