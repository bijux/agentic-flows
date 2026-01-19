# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.core.authority import authority_token, enforce_runtime_semantics
from agentic_flows.runtime.artifact_store import ArtifactStore, InMemoryArtifactStore
from agentic_flows.runtime.budget import BudgetState, ExecutionBudget
from agentic_flows.runtime.context import ExecutionContext, RunMode
from agentic_flows.runtime.execution.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.execution.live_executor import LiveExecutor
from agentic_flows.runtime.execution.observer_executor import ObserverExecutor
from agentic_flows.runtime.execution.step_executor import ExecutionOutcome, StepExecutor
from agentic_flows.runtime.observability.entropy import EntropyLedger
from agentic_flows.runtime.observability.hooks import RuntimeObserver
from agentic_flows.runtime.observability.observed_run import ObservedRun
from agentic_flows.runtime.observability.trace_recorder import TraceRecorder
from agentic_flows.runtime.orchestration.planner import ExecutionPlanner
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_arbitration import VerificationArbitration
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import FlowID


@dataclass(frozen=True)
class FlowRunResult:
    resolved_flow: ExecutionPlan
    trace: ExecutionTrace | None
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]
    verification_results: list[VerificationResult]
    verification_arbitrations: list[VerificationArbitration]


@dataclass(frozen=True)
class ExecutionConfig:
    mode: RunMode
    verification_policy: VerificationPolicy | None = None
    artifact_store: ArtifactStore | None = None
    budget: ExecutionBudget | None = None
    observed_run: ObservedRun | None = None
    parent_flow_id: FlowID | None = None
    child_flow_ids: tuple[FlowID, ...] | None = None
    observers: tuple[RuntimeObserver, ...] | None = None

    @classmethod
    def from_command(cls, command: str) -> ExecutionConfig:
        if command == "plan":
            return cls(mode=RunMode.PLAN)
        if command == "dry-run":
            return cls(mode=RunMode.DRY_RUN)
        if command == "run":
            return cls(mode=RunMode.LIVE)
        if command == "observe":
            return cls(mode=RunMode.OBSERVE)
        if command == "unsafe-run":
            return cls(mode=RunMode.UNSAFE)
        raise ValueError(f"Unsupported command: {command}")


def execute_flow(
    manifest: FlowManifest | None = None,
    *,
    resolved_flow: ExecutionPlan | None = None,
    config: ExecutionConfig | None = None,
) -> FlowRunResult:
    execution_config = config or ExecutionConfig(mode=RunMode.LIVE)
    if (manifest is None) == (resolved_flow is None):
        raise ValueError("Provide exactly one of manifest or resolved_flow")
    if resolved_flow is None:
        resolved_flow = ExecutionPlanner().resolve(manifest)

    if execution_config.mode == RunMode.PLAN:
        return FlowRunResult(
            resolved_flow=resolved_flow,
            trace=None,
            artifacts=[],
            evidence=[],
            reasoning_bundles=[],
            verification_results=[],
            verification_arbitrations=[],
        )

    if (
        execution_config.mode in {RunMode.LIVE, RunMode.OBSERVE, RunMode.UNSAFE}
        and execution_config.verification_policy is None
    ):
        raise ValueError("verification_policy is required before execution")

    strategy: StepExecutor[ExecutionPlan, ExecutionOutcome] = LiveExecutor()
    if execution_config.mode == RunMode.DRY_RUN:
        strategy = DryRunExecutor()
    if execution_config.mode == RunMode.OBSERVE:
        strategy = ObserverExecutor()

    store = execution_config.artifact_store or InMemoryArtifactStore()
    seed = _derive_seed_token(resolved_flow.plan)
    context = ExecutionContext(
        authority=authority_token(),
        seed=seed,
        environment_fingerprint=resolved_flow.plan.environment_fingerprint,
        parent_flow_id=execution_config.parent_flow_id,
        child_flow_ids=execution_config.child_flow_ids or (),
        artifact_store=store,
        trace_recorder=TraceRecorder(),
        mode=execution_config.mode,
        verification_policy=execution_config.verification_policy,
        observers=execution_config.observers or (),
        budget=BudgetState(execution_config.budget),
        entropy=EntropyLedger(resolved_flow.manifest.entropy_budget),
        _step_evidence={},
        _step_artifacts={},
        observed_run=execution_config.observed_run,
    )

    outcome = strategy.execute(resolved_flow, context)
    result = FlowRunResult(
        resolved_flow=resolved_flow,
        trace=outcome.trace,
        artifacts=outcome.artifacts,
        evidence=outcome.evidence,
        reasoning_bundles=outcome.reasoning_bundles,
        verification_results=outcome.verification_results,
        verification_arbitrations=outcome.verification_arbitrations,
    )
    enforce_runtime_semantics(result, mode=execution_config.mode.value)
    return result


def _derive_seed_token(plan: ExecutionSteps) -> str | None:
    if not plan.steps:
        return None
    for step in plan.steps:
        if not step.inputs_fingerprint:
            return None
    return plan.steps[0].inputs_fingerprint


__all__ = ["ExecutionConfig", "FlowRunResult", "RunMode", "execute_flow"]
