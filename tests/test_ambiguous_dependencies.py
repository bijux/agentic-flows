# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import pytest

from agentic_flows.runtime.run_flow import RunMode, run_flow
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import AgentID, FlowID


def test_ambiguous_dependencies_raise() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-ambiguous"),
        agents=(AgentID("agent-a"), AgentID("agent-b")),
        dependencies=("agent-a",),
        retrieval_contracts=(),
        verification_gates=(),
    )

    with pytest.raises(NotImplementedError):
        run_flow(manifest, mode=RunMode.PLAN)
