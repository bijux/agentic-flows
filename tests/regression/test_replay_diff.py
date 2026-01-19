# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.orchestration.determinism_guard import validate_replay
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ArtifactID,
    ContentHash,
    ContractID,
    EvidenceID,
    FlowID,
    GateID,
    PlanHash,
    ResolverID,
)
from agentic_flows.spec.ontology.ontology import ArtifactScope, ArtifactType
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)

pytestmark = pytest.mark.regression


def test_replay_diff_includes_artifacts_and_evidence(deterministic_environment) -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-replay-diff"),
        agents=(AgentID("alpha"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )
    result = execute_flow(manifest, config=ExecutionConfig(mode=RunMode.PLAN))
    plan = result.resolved_flow.plan

    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=plan.flow_id,
        parent_flow_id=None,
        child_flow_ids=(),
        environment_fingerprint=plan.environment_fingerprint,
        plan_hash=PlanHash("mismatch"),
        verification_policy_fingerprint=None,
        resolver_id=ResolverID("agentic-flows:v0"),
        events=(),
        tool_invocations=(),
        finalized=False,
    )
    trace.finalize()

    artifacts = [
        Artifact(
            spec_version="v1",
            artifact_id=ArtifactID("artifact-1"),
            artifact_type=ArtifactType.AGENT_INVOCATION,
            producer="agent",
            parent_artifacts=(),
            content_hash=ContentHash("hash-1"),
            scope=ArtifactScope.WORKING,
        )
    ]
    evidence = [
        RetrievedEvidence(
            spec_version="v1",
            evidence_id=EvidenceID("ev-1"),
            source_uri="file://doc",
            content_hash=ContentHash("hash-ev"),
            score=0.9,
            vector_contract_id=ContractID("contract-a"),
        )
    ]

    with pytest.raises(ValueError, match="artifact_fingerprint"):
        validate_replay(trace, plan, artifacts=artifacts, evidence=evidence)
