# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.runtime.resolver import FlowResolver
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

    with pytest.raises(NotImplementedError, match="Semantic validation not yet enforced"):
        FlowResolver().resolve(manifest)
