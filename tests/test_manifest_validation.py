# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import pytest

from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import AgentID, ContractID, FlowID, GateID


def test_invalid_manifest_rejected() -> None:
    with pytest.raises(ValueError, match="flow_id must be a non-empty string"):
        FlowManifest(
            spec_version="v1",
            flow_id=FlowID(""),
            agents=(AgentID("agent-a"),),
            dependencies=("dep-a",),
            retrieval_contracts=(ContractID("retrieval-a"),),
            verification_gates=(GateID("gate-a"),),
        )
