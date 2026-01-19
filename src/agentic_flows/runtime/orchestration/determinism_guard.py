# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from agentic_flows.runtime.observability.environment import (
    compute_environment_fingerprint,
)
from agentic_flows.runtime.observability.fingerprint import fingerprint_inputs
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.ontology.ontology import EventType


def validate_determinism(
    environment_fingerprint: str | None,
    seed: Any | None,
    unordered_normalized: bool,
) -> None:
    current_fingerprint = compute_environment_fingerprint()
    if not environment_fingerprint:
        raise ValueError("environment_fingerprint is required for deterministic runs")
    if environment_fingerprint != current_fingerprint:
        raise ValueError("environment_fingerprint mismatch")
    if seed is None:
        raise ValueError("deterministic seed is required for deterministic runs")
    if not unordered_normalized:
        raise ValueError("unordered collections must be normalized before execution")


def validate_replay(
    trace: ExecutionTrace,
    plan: ExecutionSteps,
    *,
    artifacts: Iterable[Artifact] | None = None,
    evidence: Iterable[RetrievedEvidence] | None = None,
) -> None:
    diffs = replay_diff(trace, plan, artifacts=artifacts, evidence=evidence)
    if diffs:
        raise ValueError(f"replay mismatch: {diffs}")


def replay_diff(
    trace: ExecutionTrace,
    plan: ExecutionSteps,
    *,
    artifacts: Iterable[Artifact] | None = None,
    evidence: Iterable[RetrievedEvidence] | None = None,
) -> dict[str, object]:
    diffs: dict[str, object] = {}
    if trace.plan_hash != plan.plan_hash:
        diffs["plan_hash"] = {
            "expected": plan.plan_hash,
            "observed": trace.plan_hash,
        }
    if trace.environment_fingerprint != plan.environment_fingerprint:
        diffs["environment_fingerprint"] = {
            "expected": plan.environment_fingerprint,
            "observed": trace.environment_fingerprint,
        }

    missing_step_end = _missing_step_end(trace.events, plan.steps)
    if missing_step_end:
        diffs["missing_step_end"] = sorted(missing_step_end)

    failed_steps = _failed_steps(trace.events)
    if failed_steps:
        diffs["failed_steps"] = sorted(failed_steps)

    if diffs and artifacts is not None:
        artifact_list = list(artifacts)
        diffs["artifact_fingerprint"] = semantic_artifact_fingerprint(artifact_list)
        diffs["artifact_count"] = len(artifact_list)

    if diffs and evidence is not None:
        evidence_list = list(evidence)
        diffs["evidence_fingerprint"] = semantic_evidence_fingerprint(evidence_list)
        diffs["evidence_count"] = len(evidence_list)

    return diffs


def _missing_step_end(
    events: Iterable[ExecutionEvent], steps: Iterable[object]
) -> set[int]:
    expected_steps = {step.step_index for step in steps}
    ended = {
        event.step_index for event in events if event.event_type == EventType.STEP_END
    }
    failed = _failed_steps(events)
    return expected_steps.difference(ended.union(failed))


def _failed_steps(events: Iterable[ExecutionEvent]) -> set[int]:
    failure_events = {
        EventType.REASONING_FAILED,
        EventType.RETRIEVAL_FAILED,
        EventType.STEP_FAILED,
        EventType.VERIFICATION_FAIL,
    }
    return {event.step_index for event in events if event.event_type in failure_events}


def semantic_artifact_fingerprint(artifacts: Iterable[Artifact]) -> str:
    normalized = sorted(
        artifacts, key=lambda item: (str(item.artifact_id), str(item.content_hash))
    )
    return fingerprint_inputs(
        [
            {"artifact_id": item.artifact_id, "content_hash": item.content_hash}
            for item in normalized
        ]
    )


def semantic_evidence_fingerprint(evidence: Iterable[RetrievedEvidence]) -> str:
    normalized = sorted(
        evidence, key=lambda item: (str(item.evidence_id), str(item.content_hash))
    )
    return fingerprint_inputs(
        [
            {"evidence_id": item.evidence_id, "content_hash": item.content_hash}
            for item in normalized
        ]
    )


__all__ = [
    "replay_diff",
    "semantic_artifact_fingerprint",
    "semantic_evidence_fingerprint",
    "validate_determinism",
    "validate_replay",
]
