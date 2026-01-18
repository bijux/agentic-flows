# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import AgentID, ContractID, FlowID, GateID

pytestmark = pytest.mark.unit


def test_flow_manifest_model_allows_invalid_state() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID(""),
        agents=(AgentID(""),),
        dependencies=("invalid",),
        retrieval_contracts=(ContractID(""),),
        verification_gates=(GateID(""),),
    )

    assert manifest.flow_id == ""
