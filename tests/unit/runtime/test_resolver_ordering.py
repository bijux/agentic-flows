# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.resolver import FlowResolver
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import AgentID, FlowID

pytestmark = pytest.mark.unit


def test_resolver_uses_lexical_tiebreak_for_ordering() -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-ordering"),
        agents=(AgentID("bravo"), AgentID("alpha")),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    resolved = FlowResolver().resolve(manifest)
    ordered = [step.agent_id for step in resolved.plan.steps]

    assert ordered == [AgentID("alpha"), AgentID("bravo")]
