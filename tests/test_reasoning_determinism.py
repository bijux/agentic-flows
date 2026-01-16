import json
from dataclasses import asdict

import bijux_rar

from agentic_flows.runtime.reasoning_executor import ReasoningExecutor
from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence


def test_reasoning_determinism() -> None:
    def _deterministic_reason(agent_outputs, evidence, seed):
        return ReasoningBundle(
            bundle_id=f"bundle-{seed}",
            claims=[
                ReasoningClaim(
                    claim_id="claim-1",
                    statement="statement",
                    confidence=0.5,
                    supported_by=[evidence[0].evidence_id],
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
            evidence_ids=[evidence[0].evidence_id],
            producer_agent_id=agent_outputs[0].artifact_id,
        )

    bijux_rar.reason = _deterministic_reason

    agent_outputs = [
        Artifact(
            artifact_id="agent-output",
            artifact_type="output",
            producer="agent",
            parent_artifacts=(),
            content_hash="hash",
        )
    ]
    evidence = [
        RetrievedEvidence(
            evidence_id="ev-1",
            source_uri="file://doc-1",
            content_hash="hash-1",
            score=0.9,
            vector_contract_id="contract-1",
        )
    ]

    executor = ReasoningExecutor()
    bundle_one = executor.execute(agent_outputs, evidence)
    bundle_two = executor.execute(agent_outputs, evidence)

    payload_one = json.dumps(asdict(bundle_one), sort_keys=True)
    payload_two = json.dumps(asdict(bundle_two), sort_keys=True)

    assert payload_one == payload_two
