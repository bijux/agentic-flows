# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentic_flows.runtime.artifact_store import ArtifactStore, InMemoryArtifactStore
from agentic_flows.runtime.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.live_executor import LiveExecutor
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.execution_trace import ExecutionTrace
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.resolved_flow import ResolvedFlow
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.verification import VerificationPolicy
from agentic_flows.spec.verification_result import VerificationResult


class RunMode(str, Enum):
    PLAN = "plan"
    DRY_RUN = "dry-run"
    LIVE = "live"


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

    store = artifact_store or InMemoryArtifactStore()

    if mode == RunMode.DRY_RUN:
        trace = DryRunExecutor().execute(resolved_flow)
        return FlowRunResult(
            resolved_flow=resolved_flow,
            trace=trace,
            artifacts=[],
            evidence=[],
            reasoning_bundles=[],
            verification_results=[],
        )

    trace, artifacts, evidence, reasoning_bundles, verification_results = (
        LiveExecutor().execute(
            resolved_flow,
            verification_policy=verification_policy,
            artifact_store=store,
        )
    )
    return FlowRunResult(
        resolved_flow=resolved_flow,
        trace=trace,
        artifacts=artifacts,
        evidence=evidence,
        reasoning_bundles=reasoning_bundles,
        verification_results=verification_results,
    )


__all__ = ["FlowRunResult", "RunMode", "run_flow"]
