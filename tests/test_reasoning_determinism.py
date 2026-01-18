# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import json
from dataclasses import asdict

import bijux_rar

from agentic_flows.runtime.reasoning_executor import ReasoningExecutor
from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.artifact_types import ArtifactType
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.ids import (
    AgentID,
    ArtifactID,
    BundleID,
    ClaimID,
    ContentHash,
    ContractID,
    EvidenceID,
    StepID,
)


def test_reasoning_determinism() -> None:
    def _deterministic_reason(agent_outputs, evidence, seed):
        return ReasoningBundle(
            spec_version="v1",
            bundle_id=BundleID(f"bundle-{seed}"),
            claims=(
                ReasoningClaim(
                    spec_version="v1",
                    claim_id=ClaimID("claim-1"),
                    statement="statement",
                    confidence=0.5,
                    supported_by=(evidence[0].evidence_id,),
                ),
            ),
            steps=(
                ReasoningStep(
                    spec_version="v1",
                    step_id=StepID("step-1"),
                    input_claims=(),
                    output_claims=(ClaimID("claim-1"),),
                    method="aggregation",
                ),
            ),
            evidence_ids=(evidence[0].evidence_id,),
            producer_agent_id=AgentID("agent-a"),
        )

    bijux_rar.reason = _deterministic_reason

    agent_outputs = [
        Artifact(
            spec_version="v1",
            artifact_id=ArtifactID("agent-output"),
            artifact_type=ArtifactType.AGENT_INVOCATION,
            producer="agent",
            parent_artifacts=(),
            content_hash=ContentHash("hash"),
        )
    ]
    evidence = [
        RetrievedEvidence(
            spec_version="v1",
            evidence_id=EvidenceID("ev-1"),
            source_uri="file://doc-1",
            content_hash=ContentHash("hash-1"),
            score=0.9,
            vector_contract_id=ContractID("contract-1"),
        )
    ]

    executor = ReasoningExecutor()
    bundle_one = executor.execute(agent_outputs, evidence)
    bundle_two = executor.execute(agent_outputs, evidence)

    payload_one = json.dumps(asdict(bundle_one), sort_keys=True)
    payload_two = json.dumps(asdict(bundle_two), sort_keys=True)

    assert payload_one == payload_two
