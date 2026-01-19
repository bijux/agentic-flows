# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_rag
import bijux_vex
import pytest

from agentic_flows.runtime.observability.trace_diff import entropy_summary
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.model.retrieval_request import RetrievalRequest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    FlowID,
    GateID,
    InputsFingerprint,
    RequestID,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EvidenceDeterminism,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
    StepType,
)

pytestmark = pytest.mark.regression


def test_entropy_canary_stable_sources(
    baseline_policy, resolved_flow_factory, replay_envelope, dataset_descriptor
) -> None:
    bijux_rag.retrieve = lambda **_kwargs: [
        {
            "evidence_id": "ev-entropy",
            "determinism": EvidenceDeterminism.EXTERNAL.value,
            "source_uri": "file://doc",
            "content": "content",
            "score": 0.9,
            "vector_contract_id": "contract-1",
        }
    ]
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: True

    request = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-entropy"),
        query="entropy",
        vector_contract_id=ContractID("contract-1"),
        top_k=1,
        scope="project",
    )
    step = ResolvedStep(
        spec_version="v1",
        step_index=0,
        step_type=StepType.AGENT,
        determinism_level=DeterminismLevel.STRICT,
        agent_id=AgentID("agent-a"),
        inputs_fingerprint=InputsFingerprint("inputs"),
        declared_dependencies=(),
        expected_artifacts=(),
        agent_invocation=AgentInvocation(
            spec_version="v1",
            agent_id=AgentID("agent-a"),
            agent_version=VersionID("0.0.0"),
            inputs_fingerprint=InputsFingerprint("inputs"),
            declared_outputs=(),
            execution_mode="seeded",
        ),
        retrieval_request=request,
    )
    entropy_budget = EntropyBudget(
        spec_version="v1",
        allowed_sources=(EntropySource.SEEDED_RNG, EntropySource.DATA),
        max_magnitude=EntropyMagnitude.HIGH,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-entropy"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        replay_envelope=replay_envelope,
        dataset=dataset_descriptor,
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-1"),),
        verification_gates=(GateID("gate-a"),),
    )
    resolved_flow = resolved_flow_factory(manifest, (step,))
    first = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    second = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.LIVE, verification_policy=baseline_policy),
    )
    summary_one = entropy_summary(first.trace.entropy_usage)
    summary_two = entropy_summary(second.trace.entropy_usage)

    assert summary_one == summary_two
    assert "data" in summary_one["sources"]
