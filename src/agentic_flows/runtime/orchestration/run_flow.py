# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.runtime.artifact_store import ArtifactStore, InMemoryArtifactStore
from agentic_flows.runtime.context import RunMode, RuntimeContext
from agentic_flows.runtime.execution.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.execution.live_executor import LiveExecutor
from agentic_flows.runtime.execution.strategy import ExecutionStrategy
from agentic_flows.runtime.orchestration.resolver import FlowResolver
from agentic_flows.runtime.semantics import enforce_runtime_semantics
from agentic_flows.runtime.trace_recorder import TraceRecorder
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.resolved_flow import ResolvedFlow
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_result import VerificationResult


@dataclass(frozen=True)
class FlowRunResult:
    resolved_flow: ResolvedFlow
    trace: ExecutionTrace | None
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]
    verification_results: list[VerificationResult]


def run_flow(
    manifest: FlowManifest | None = None,
    *,
    resolved_flow: ResolvedFlow | None = None,
    mode: RunMode = RunMode.LIVE,
    verification_policy: VerificationPolicy | None = None,
    artifact_store: ArtifactStore | None = None,
) -> FlowRunResult:
    if (manifest is None) == (resolved_flow is None):
        raise ValueError("Provide exactly one of manifest or resolved_flow")
    if resolved_flow is None:
        resolved_flow = FlowResolver().resolve(manifest)

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

    strategy: ExecutionStrategy = LiveExecutor()
    if mode == RunMode.DRY_RUN:
        strategy = DryRunExecutor()

    store = artifact_store or InMemoryArtifactStore()
    context = RuntimeContext(
        environment_fingerprint=resolved_flow.plan.environment_fingerprint,
        artifact_store=store,
        trace_recorder=TraceRecorder(),
        run_mode=mode,
        verification_policy=verification_policy,
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
    enforce_runtime_semantics(result, mode=mode)
    return result


__all__ = ["FlowRunResult", "RunMode", "run_flow"]
