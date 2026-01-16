import json
from dataclasses import asdict
from pathlib import Path

from agentic_flows.runtime import resolver as resolver_module
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest


def test_golden_execution_plan(monkeypatch) -> None:
    manifest = FlowManifest(
        flow_id="flow-golden",
        agents=("alpha", "bravo", "charlie"),
        dependencies=("bravo:alpha", "charlie:alpha"),
        retrieval_contracts=("contract-a",),
        verification_gates=("gate-a",),
    )

    monkeypatch.setattr(resolver_module, "compute_environment_fingerprint", lambda: "env-fingerprint")
    resolver = FlowResolver()
    resolver._bijux_cli_version = "0.0.0"
    resolver._bijux_agent_version = "0.0.0"

    plan = resolver.resolve(manifest)
    payload = json.dumps(asdict(plan), sort_keys=True)

    golden_path = Path(__file__).parent / "golden" / "test_execution_plan.json"
    expected = golden_path.read_text(encoding="utf-8").strip()
    assert payload == expected
