# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from agentic_flows.runtime.observability.environment import (
    compute_environment_fingerprint,
)
from agentic_flows.runtime.observability.fingerprint import (
    fingerprint_inputs,
    fingerprint_policy,
)
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.ontology import DeterminismLevel
from agentic_flows.spec.ontology.public import (
    EventType,
    ReplayAcceptability,
)


def validate_determinism(
    environment_fingerprint: str | None,
    seed: Any | None,
    unordered_normalized: bool,
    determinism_level: DeterminismLevel,
) -> None:
    """Input contract: environment_fingerprint is provided for the running host, seed is set when required, and unordered_normalized reflects input normalization; output guarantee: returns None when inputs satisfy the determinism_level requirements; failure semantics: raises ValueError on missing fingerprints, mismatches, or required normalization/seed violations."""
    current_fingerprint = compute_environment_fingerprint()
    if not environment_fingerprint:
        raise ValueError("environment_fingerprint is required before execution")
    if environment_fingerprint != current_fingerprint:
        raise ValueError("environment_fingerprint mismatch")
    if determinism_level in {DeterminismLevel.STRICT, DeterminismLevel.BOUNDED}:
        if seed is None:
            raise ValueError("deterministic seed is required for strict runs")
        if not unordered_normalized:
            raise ValueError(
                "unordered collections must be normalized before execution"
            )
    elif determinism_level == DeterminismLevel.PROBABILISTIC:
        if not unordered_normalized:
            raise ValueError(
                "unordered collections must be normalized before execution"
            )


def validate_replay(
    trace: ExecutionTrace,
    plan: ExecutionSteps,
    *,
    artifacts: Iterable[Artifact] | None = None,
    evidence: Iterable[RetrievedEvidence] | None = None,
    verification_policy: object | None = None,
) -> None:
    """Validate replay; misuse breaks acceptability checks."""
    diffs = replay_diff(
        trace,
        plan,
        artifacts=artifacts,
        evidence=evidence,
        verification_policy=verification_policy,
    )
    blocking, acceptable = _partition_diffs(diffs, plan.replay_acceptability)
    if blocking:
        detail = {"blocking": blocking}
        if acceptable:
            detail["acceptable"] = acceptable
        raise ValueError(f"replay mismatch: {detail}")


def replay_diff(
    trace: ExecutionTrace,
    plan: ExecutionSteps,
    *,
    artifacts: Iterable[Artifact] | None = None,
    evidence: Iterable[RetrievedEvidence] | None = None,
    verification_policy: object | None = None,
) -> dict[str, object]:
    """Input contract: trace and plan describe the same run boundary and are finalized for comparison; output guarantee: returns a diff map of all contract mismatches across plan, environment, dataset, artifacts, evidence, and policy; failure semantics: does not raise and reports violations via the returned diff map."""
    diffs: dict[str, object] = {}
    if trace.plan_hash != plan.plan_hash:
        diffs["plan_hash"] = {
            "expected": plan.plan_hash,
            "observed": trace.plan_hash,
        }
    if trace.determinism_level != plan.determinism_level:
        diffs["determinism_level"] = {
            "expected": plan.determinism_level,
            "observed": trace.determinism_level,
        }
    if trace.replay_acceptability != plan.replay_acceptability:
        diffs["replay_acceptability"] = {
            "expected": plan.replay_acceptability,
            "observed": trace.replay_acceptability,
        }
    if trace.tenant_id != plan.tenant_id:
        diffs["tenant_id"] = {
            "expected": plan.tenant_id,
            "observed": trace.tenant_id,
        }
    if trace.flow_state != plan.flow_state:
        diffs["flow_state"] = {
            "expected": plan.flow_state,
            "observed": trace.flow_state,
        }
    if trace.replay_envelope != plan.replay_envelope:
        diffs["replay_envelope"] = {
            "expected": _envelope_payload(plan.replay_envelope),
            "observed": _envelope_payload(trace.replay_envelope),
        }
    if trace.environment_fingerprint != plan.environment_fingerprint:
        diffs["environment_fingerprint"] = {
            "expected": plan.environment_fingerprint,
            "observed": trace.environment_fingerprint,
        }
    if trace.dataset != plan.dataset:
        diffs["dataset"] = {
            "expected": _dataset_payload(plan.dataset),
            "observed": _dataset_payload(trace.dataset),
        }
    if trace.allow_deprecated_datasets != plan.allow_deprecated_datasets:
        diffs["allow_deprecated_datasets"] = {
            "expected": plan.allow_deprecated_datasets,
            "observed": trace.allow_deprecated_datasets,
        }
    if (
        plan.dataset.dataset_state.value == "deprecated"
        and not plan.allow_deprecated_datasets
    ):
        diffs["deprecated_dataset"] = {
            "expected": False,
            "observed": True,
        }

    if trace.verification_policy_fingerprint is not None:
        if verification_policy is None:
            diffs["verification_policy"] = {
                "expected": trace.verification_policy_fingerprint,
                "observed": None,
            }
        else:
            current = fingerprint_policy(verification_policy)
            if current != trace.verification_policy_fingerprint:
                diffs["verification_policy"] = {
                    "expected": trace.verification_policy_fingerprint,
                    "observed": current,
                }

    missing_step_end = _missing_step_end(trace.events, plan.steps)
    if missing_step_end:
        diffs["missing_step_end"] = sorted(missing_step_end)

    failed_steps = _failed_steps(trace.events)
    if failed_steps:
        diffs["failed_steps"] = sorted(failed_steps)

    human_events = _human_intervention_events(trace.events)
    if human_events:
        diffs["human_intervention_events"] = human_events

    if diffs and artifacts is not None:
        artifact_list = list(artifacts)
        diffs["artifact_fingerprint"] = semantic_artifact_fingerprint(artifact_list)
        diffs["artifact_count"] = len(artifact_list)

    if diffs and evidence is not None:
        evidence_list = list(evidence)
        diffs["evidence_fingerprint"] = semantic_evidence_fingerprint(evidence_list)
        diffs["evidence_count"] = len(evidence_list)

    if diffs:
        primary = next(iter(diffs))
        diffs["summary"] = f"Replay rejected: {primary}"

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


def _human_intervention_events(events: Iterable[ExecutionEvent]) -> list[int]:
    return [
        event.event_index
        for event in events
        if event.event_type == EventType.HUMAN_INTERVENTION
    ]


def semantic_artifact_fingerprint(artifacts: Iterable[Artifact]) -> str:
    """Fingerprint artifacts; misuse breaks replay comparison."""
    normalized = sorted(
        artifacts,
        key=lambda item: (
            str(item.tenant_id),
            str(item.artifact_id),
            str(item.content_hash),
        ),
    )
    return fingerprint_inputs(
        [
            {
                "tenant_id": item.tenant_id,
                "artifact_id": item.artifact_id,
                "content_hash": item.content_hash,
            }
            for item in normalized
        ]
    )


def semantic_evidence_fingerprint(evidence: Iterable[RetrievedEvidence]) -> str:
    """Fingerprint evidence; misuse breaks replay comparison."""
    normalized = sorted(
        evidence, key=lambda item: (str(item.evidence_id), str(item.content_hash))
    )
    return fingerprint_inputs(
        [
            {
                "evidence_id": item.evidence_id,
                "content_hash": item.content_hash,
                "determinism": item.determinism,
            }
            for item in normalized
        ]
    )


def _partition_diffs(
    diffs: dict[str, object], acceptability: ReplayAcceptability
) -> tuple[dict[str, object], dict[str, object]]:
    # ReplayAcceptability.EXACT_MATCH: triggers on any divergence; acceptable in production: yes.
    # ReplayAcceptability.INVARIANT_PRESERVING: triggers when only invariant-safe deltas exist; acceptable in production: yes.
    # ReplayAcceptability.STATISTICALLY_BOUNDED: triggers when bounded statistical drift is present; acceptable in production: depends on policy.
    if not diffs:
        return {}, {}
    allowed: set[str] = set()
    if acceptability in {
        ReplayAcceptability.INVARIANT_PRESERVING,
        ReplayAcceptability.STATISTICALLY_BOUNDED,
    }:
        allowed = {
            "events",
            "artifact_fingerprint",
            "artifact_count",
            "evidence_fingerprint",
            "evidence_count",
        }
    blocking = {key: value for key, value in diffs.items() if key not in allowed}
    acceptable = {key: value for key, value in diffs.items() if key in allowed}
    return blocking, acceptable


def _dataset_payload(dataset) -> dict[str, object]:
    return {
        "dataset_id": dataset.dataset_id,
        "tenant_id": dataset.tenant_id,
        "dataset_version": dataset.dataset_version,
        "dataset_hash": dataset.dataset_hash,
        "dataset_state": dataset.dataset_state,
    }


def _envelope_payload(envelope) -> dict[str, object]:
    return {
        "min_claim_overlap": envelope.min_claim_overlap,
        "max_contradiction_delta": envelope.max_contradiction_delta,
    }


__all__ = [
    "replay_diff",
    "semantic_artifact_fingerprint",
    "semantic_evidence_fingerprint",
    "validate_determinism",
    "validate_replay",
]
