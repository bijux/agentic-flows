# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.core.semantics import enforce_runtime_semantics
from agentic_flows.runtime.artifact_store import ArtifactStore, InMemoryArtifactStore
from agentic_flows.runtime.context import ExecutionContext, RunMode
from agentic_flows.runtime.execution.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.execution.live_executor import LiveExecutor
from agentic_flows.runtime.execution.step_executor import StepExecutor
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
from agentic_flows.spec.model.verification_result import VerificationResult


@dataclass(frozen=True)
class FlowRunResult:
    resolved_flow: ExecutionPlan
    trace: ExecutionTrace | None
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]
    verification_results: list[VerificationResult]


def execute_flow(
    manifest: FlowManifest | None = None,
    *,
    resolved_flow: ExecutionPlan | None = None,
    mode: RunMode = RunMode.LIVE,
    verification_policy: VerificationPolicy | None = None,
    artifact_store: ArtifactStore | None = None,
) -> FlowRunResult:
    if (manifest is None) == (resolved_flow is None):
        raise ValueError("Provide exactly one of manifest or resolved_flow")
    if resolved_flow is None:
        resolved_flow = ExecutionPlanner().resolve(manifest)

    if mode == RunMode.PLAN:
        return FlowRunResult(
            resolved_flow=resolved_flow,
            trace=None,
            artifacts=[],
            evidence=[],
            reasoning_bundles=[],
            verification_results=[],
        )

    if verification_policy is None:
        raise ValueError("verification_policy is required before execution")

    strategy: StepExecutor[ExecutionPlan] = LiveExecutor()
    if mode == RunMode.DRY_RUN:
        strategy = DryRunExecutor()

    store = artifact_store or InMemoryArtifactStore()
    seed = _derive_seed_token(resolved_flow.plan)
    context = ExecutionContext(
        seed=seed,
        environment_fingerprint=resolved_flow.plan.environment_fingerprint,
        artifact_store=store,
        trace_recorder=TraceRecorder(),
        mode=mode,
        verification_policy=verification_policy,
        step_evidence={},
        step_artifacts={},
    )

    outcome = strategy.execute(resolved_flow, context)
    result = FlowRunResult(
        resolved_flow=resolved_flow,
        trace=outcome.trace,
        artifacts=outcome.artifacts,
        evidence=outcome.evidence,
        reasoning_bundles=outcome.reasoning_bundles,
        verification_results=outcome.verification_results,
    )
    enforce_runtime_semantics(result, mode=mode.value)
    return result


def _derive_seed_token(plan: ExecutionSteps) -> str | None:
    if not plan.steps:
        return None
    for step in plan.steps:
        if not step.inputs_fingerprint:
            return None
    return plan.steps[0].inputs_fingerprint


__all__ = ["FlowRunResult", "RunMode", "execute_flow"]
