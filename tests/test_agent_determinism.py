import json
from dataclasses import asdict

import bijux_agent
import bijux_rar

from agentic_flows.runtime import resolver as resolver_module
from agentic_flows.runtime.live_executor import LiveExecutor
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep


def test_agent_determinism() -> None:
    manifest = FlowManifest(
        flow_id="flow-live",
        agents=("agent-a",),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    def _deterministic_run(agent_id, seed, inputs_fingerprint, declared_outputs, **_kwargs):
        return [
            {
                "artifact_id": f"{agent_id}-artifact",
                "artifact_type": "output",
                "content": f"{seed}:{inputs_fingerprint}:{declared_outputs}",
                "parent_artifacts": [],
            }
        ]

    bijux_agent.run = _deterministic_run
    bijux_rar.reason = lambda **_kwargs: ReasoningBundle(
        bundle_id="bundle-1",
        claims=[
            ReasoningClaim(
                claim_id="claim-1",
                statement="statement",
                confidence=0.5,
                supported_by=[],
            )
        ],
        steps=[
            ReasoningStep(
                step_id="step-1",
                input_claims=[],
                output_claims=["claim-1"],
                method="aggregation",
            )
        ],
        evidence_ids=[],
        producer_agent_id="agent-a",
    )

    resolver_module.compute_environment_fingerprint = lambda: "env-fingerprint"
    resolver = FlowResolver()
    resolver._bijux_agent_version = "0.0.0"

    executor = LiveExecutor()

    plan_one = resolver.resolve(manifest)
    trace_one, artifacts_one, _, _, _ = executor.execute(plan_one)
    payload_one = json.dumps(asdict(trace_one), sort_keys=True)

    plan_two = resolver.resolve(manifest)
    trace_two, artifacts_two, _, _, _ = executor.execute(plan_two)
    payload_two = json.dumps(asdict(trace_two), sort_keys=True)

    assert payload_one == payload_two
    assert [artifact.content_hash for artifact in artifacts_one] == [
        artifact.content_hash for artifact in artifacts_two
    ]
