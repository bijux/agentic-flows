import pytest

from agentic_flows.runtime import resolver as resolver_module
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest


def test_ambiguous_dependencies_raise() -> None:
    manifest = FlowManifest(
        flow_id="flow-ambiguous",
        agents=("agent-a", "agent-b"),
        dependencies=("agent-a",),
        retrieval_contracts=(),
        verification_gates=(),
    )

    resolver = FlowResolver()
    resolver._bijux_agent_version = "0.0.0"
    resolver_module.compute_environment_fingerprint = lambda: "env-fingerprint"
    with pytest.raises(ValueError):
        resolver.resolve(manifest)
