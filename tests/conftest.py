# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import sys
import types

import pytest

from agentic_flows.runtime.artifact_store import InMemoryArtifactStore
from agentic_flows.runtime.observability.environment import (
    compute_environment_fingerprint,
)
from agentic_flows.runtime.observability.fingerprint import fingerprint_inputs
from agentic_flows.spec.model.agent_invocation import AgentInvocation
from agentic_flows.spec.model.arbitration_policy import ArbitrationPolicy
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    DatasetID,
    EnvironmentFingerprint,
    FlowID,
    GateID,
    InputsFingerprint,
    PlanHash,
    ResolverID,
    VersionID,
)
from agentic_flows.spec.ontology.ontology import (
    ArbitrationRule,
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
    StepType,
    VerificationRandomness,
)


def pytest_configure() -> None:
    if "bijux_cli" not in sys.modules:
        stub = types.ModuleType("bijux_cli")
        stub.__version__ = "0.0.0"
        sys.modules["bijux_cli"] = stub
    if "bijux_agent" not in sys.modules:
        stub = types.ModuleType("bijux_agent")
        stub.__version__ = "0.0.0"
        stub.run = lambda **_kwargs: []
        sys.modules["bijux_agent"] = stub
    if "bijux_rag" not in sys.modules:
        stub = types.ModuleType("bijux_rag")
        stub.retrieve = lambda **_kwargs: []
        sys.modules["bijux_rag"] = stub
    if "bijux_vex" not in sys.modules:
        stub = types.ModuleType("bijux_vex")
        stub.enforce_contract = lambda *_args, **_kwargs: True
        sys.modules["bijux_vex"] = stub
    if "bijux_rar" not in sys.modules:
        stub = types.ModuleType("bijux_rar")
        stub.reason = lambda **_kwargs: None
        sys.modules["bijux_rar"] = stub


@pytest.fixture(autouse=True)
def stable_bijux_versions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agentic_flows.runtime.orchestration.planner.ExecutionPlanner._bijux_cli_version",
        "0.0.0",
        raising=False,
    )
    monkeypatch.setattr(
        "agentic_flows.runtime.orchestration.planner.ExecutionPlanner._bijux_agent_version",
        "0.0.0",
        raising=False,
    )


@pytest.fixture
def baseline_policy() -> VerificationPolicy:
    return VerificationPolicy(
        spec_version="v1",
        verification_level="baseline",
        failure_mode="halt",
        randomness_tolerance=VerificationRandomness.DETERMINISTIC,
        arbitration_policy=ArbitrationPolicy(
            spec_version="v1",
            rule=ArbitrationRule.UNANIMOUS,
            quorum_threshold=None,
        ),
        required_evidence=(),
        rules=(),
        fail_on=(),
        escalate_on=(),
    )


@pytest.fixture
def artifact_store() -> InMemoryArtifactStore:
    return InMemoryArtifactStore()


@pytest.fixture
def entropy_budget() -> EntropyBudget:
    return EntropyBudget(
        spec_version="v1",
        allowed_sources=(EntropySource.SEEDED_RNG, EntropySource.DATA),
        max_magnitude=EntropyMagnitude.LOW,
    )


@pytest.fixture
def replay_envelope() -> ReplayEnvelope:
    return ReplayEnvelope(
        spec_version="v1",
        min_claim_overlap=0.8,
        max_contradiction_delta=0,
        require_same_arbitration=True,
    )


@pytest.fixture
def dataset_descriptor() -> DatasetDescriptor:
    return DatasetDescriptor(
        spec_version="v1",
        dataset_id=DatasetID("retrieval_corpus"),
        dataset_version="1.0.0",
        dataset_hash="136275faf776ff9aae3823d7d6f928e9",
    )


@pytest.fixture
def deterministic_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> EnvironmentFingerprint:
    fingerprint = EnvironmentFingerprint("env-fingerprint")
    monkeypatch.setattr(
        "agentic_flows.runtime.observability.environment.compute_environment_fingerprint",
        lambda: fingerprint,
    )
    monkeypatch.setattr(
        "agentic_flows.runtime.orchestration.planner.compute_environment_fingerprint",
        lambda: fingerprint,
    )
    monkeypatch.setattr(
        "agentic_flows.runtime.orchestration.determinism_guard.compute_environment_fingerprint",
        lambda: fingerprint,
    )
    return fingerprint


@pytest.fixture
def plan_hash_for():
    def _plan_hash_for(
        flow_id: str,
        steps: tuple[ResolvedStep, ...],
        dependencies: dict[str, list[str]],
        *,
        determinism_level: DeterminismLevel,
        replay_acceptability: ReplayAcceptability,
        entropy_budget: EntropyBudget,
        replay_envelope: ReplayEnvelope,
        dataset,
    ) -> PlanHash:
        payload = {
            "flow_id": flow_id,
            "determinism_level": determinism_level,
            "replay_acceptability": replay_acceptability,
            "entropy_budget": {
                "allowed_sources": list(entropy_budget.allowed_sources),
                "max_magnitude": entropy_budget.max_magnitude,
            },
            "replay_envelope": {
                "min_claim_overlap": replay_envelope.min_claim_overlap,
                "max_contradiction_delta": replay_envelope.max_contradiction_delta,
                "require_same_arbitration": replay_envelope.require_same_arbitration,
            },
            "dataset": {
                "dataset_id": getattr(dataset, "dataset_id", None),
                "dataset_version": getattr(dataset, "dataset_version", None),
                "dataset_hash": getattr(dataset, "dataset_hash", None),
            },
            "steps": [
                {
                    "index": step.step_index,
                    "agent_id": step.agent_id,
                    "inputs_fingerprint": step.inputs_fingerprint,
                    "declared_dependencies": list(step.declared_dependencies),
                    "step_type": step.step_type,
                    "determinism_level": step.determinism_level,
                }
                for step in steps
            ],
            "dependencies": {
                agent_id: sorted(deps) for agent_id, deps in dependencies.items()
            },
        }
        return PlanHash(fingerprint_inputs(payload))

    return _plan_hash_for


@pytest.fixture
def resolved_flow(
    deterministic_environment,
    plan_hash_for,
    entropy_budget,
    replay_envelope,
    dataset_descriptor,
) -> ExecutionPlan:
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
        retrieval_request=None,
    )
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-fixture"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        replay_envelope=replay_envelope,
        dataset=dataset_descriptor,
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(ContractID("contract-a"),),
        verification_gates=(GateID("gate-a"),),
    )
    plan = ExecutionSteps(
        spec_version="v1",
        flow_id=FlowID("flow-fixture"),
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=entropy_budget,
        replay_envelope=replay_envelope,
        dataset=dataset_descriptor,
        steps=(step,),
        environment_fingerprint=deterministic_environment,
        plan_hash=plan_hash_for(
            "flow-fixture",
            (step,),
            {},
            determinism_level=manifest.determinism_level,
            replay_acceptability=manifest.replay_acceptability,
            entropy_budget=manifest.entropy_budget,
            replay_envelope=manifest.replay_envelope,
            dataset=manifest.dataset,
        ),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    return ExecutionPlan(spec_version="v1", manifest=manifest, plan=plan)


@pytest.fixture
def resolved_flow_factory(plan_hash_for, entropy_budget):
    def _factory(
        manifest: FlowManifest,
        steps: tuple[ResolvedStep, ...],
        *,
        environment_fingerprint: EnvironmentFingerprint | None = None,
        dependencies: dict[str, list[str]] | None = None,
    ) -> ExecutionPlan:
        fingerprint = environment_fingerprint or EnvironmentFingerprint(
            compute_environment_fingerprint()
        )
        deps = dependencies or {}
        plan = ExecutionSteps(
            spec_version="v1",
            flow_id=FlowID(manifest.flow_id),
            determinism_level=manifest.determinism_level,
            replay_acceptability=manifest.replay_acceptability,
            entropy_budget=manifest.entropy_budget,
            replay_envelope=manifest.replay_envelope,
            dataset=manifest.dataset,
            steps=steps,
            environment_fingerprint=fingerprint,
            plan_hash=plan_hash_for(
                manifest.flow_id,
                steps,
                deps,
                determinism_level=manifest.determinism_level,
                replay_acceptability=manifest.replay_acceptability,
                entropy_budget=manifest.entropy_budget,
                replay_envelope=manifest.replay_envelope,
                dataset=manifest.dataset,
            ),
            resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
        )
        return ExecutionPlan(spec_version="v1", manifest=manifest, plan=plan)

    return _factory
