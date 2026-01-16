import pytest

from agentic_flows.spec.flow_manifest import FlowManifest


def test_invalid_manifest_rejected() -> None:
    with pytest.raises(ValueError):
        FlowManifest(
            flow_id="",
            agents=("agent-a",),
            dependencies=("dep-a",),
            retrieval_contracts=("retrieval-a",),
            verification_gates=("gate-a",),
        )
