# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.contracts.flow_contract import validate
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import AgentID, ContractID, FlowID, GateID

pytestmark = pytest.mark.unit


def test_invalid_manifest_rejected() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID(""),
        agents=(AgentID("agent-a"),),
        dependencies=("dep-a",),
        retrieval_contracts=(ContractID("retrieval-a"),),
        verification_gates=(GateID("gate-a"),),
    )

    with pytest.raises(ValueError, match="flow_id must be a non-empty string"):
        validate(manifest)
