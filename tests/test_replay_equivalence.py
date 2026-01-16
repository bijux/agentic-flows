import json
from dataclasses import asdict

from agentic_flows.runtime import resolver as resolver_module
from agentic_flows.runtime.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest


def test_replay_equivalence() -> None:
    manifest = FlowManifest(
        flow_id="flow-replay",
        agents=("alpha", "bravo"),
        dependencies=("bravo:alpha",),
        retrieval_contracts=("contract-a",),
        verification_gates=("gate-a",),
    )

    resolver_module.compute_environment_fingerprint = lambda: "env-fingerprint"
    resolver = FlowResolver()
    resolver._bijux_agent_version = "0.0.0"
    executor = DryRunExecutor()

    plan_one = resolver.resolve(manifest)
    trace_one = executor.execute(plan_one)
    payload_one = json.dumps(asdict(trace_one), sort_keys=True)

    plan_two = resolver.resolve(manifest)
    trace_two = executor.execute(plan_two)
    payload_two = json.dumps(asdict(trace_two), sort_keys=True)

    assert payload_one == payload_two
