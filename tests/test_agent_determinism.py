# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import AgentID, FlowID


def test_agent_determinism() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-live"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    resolver = FlowResolver()
    with pytest.raises(NotImplementedError):
        resolver.resolve(manifest)
