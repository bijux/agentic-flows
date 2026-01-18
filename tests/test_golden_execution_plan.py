# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import AgentID, ContractID, FlowID, GateID


def test_golden_execution_plan() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-golden"),
        agents=(AgentID("alpha"), AgentID("bravo"), AgentID("charlie")),
        dependencies=("bravo:alpha", "charlie:alpha"),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )

    resolver = FlowResolver()
    with pytest.raises(NotImplementedError):
        resolver.resolve(manifest)
