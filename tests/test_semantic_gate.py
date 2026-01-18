# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import pytest

from agentic_flows.runtime.run_flow import RunMode, run_flow
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import AgentID, FlowID


def test_semantic_gate_blocks_execution() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-semantic-gate"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    with pytest.raises(
        NotImplementedError, match="Semantic validation not yet enforced"
    ):
        run_flow(manifest, mode=RunMode.PLAN)
