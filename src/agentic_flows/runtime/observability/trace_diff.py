# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology.ontology import ReplayAcceptability


def semantic_trace_diff(
    expected: ExecutionTrace,
    observed: ExecutionTrace,
    *,
    acceptability: ReplayAcceptability = ReplayAcceptability.EXACT_MATCH,
) -> dict[str, object]:
    diffs: dict[str, object] = {}
    if expected.flow_id != observed.flow_id:
        diffs["flow_id"] = {"expected": expected.flow_id, "observed": observed.flow_id}
    if expected.plan_hash != observed.plan_hash:
        diffs["plan_hash"] = {
            "expected": expected.plan_hash,
            "observed": observed.plan_hash,
        }
    if expected.environment_fingerprint != observed.environment_fingerprint:
        diffs["environment_fingerprint"] = {
            "expected": expected.environment_fingerprint,
            "observed": observed.environment_fingerprint,
        }
    if (
        expected.verification_policy_fingerprint
        != observed.verification_policy_fingerprint
    ):
        diffs["verification_policy_fingerprint"] = {
            "expected": expected.verification_policy_fingerprint,
            "observed": observed.verification_policy_fingerprint,
        }
    expected_events = _event_signature(expected, acceptability)
    observed_events = _event_signature(observed, acceptability)
    if expected_events != observed_events:
        diffs["events"] = {
            "expected": expected_events,
            "observed": observed_events,
        }
    elif acceptability != ReplayAcceptability.EXACT_MATCH and _event_signature(
        expected, ReplayAcceptability.EXACT_MATCH
    ) != _event_signature(observed, ReplayAcceptability.EXACT_MATCH):
        diffs["acceptable_events"] = "different but acceptable under policy"
    return diffs


def render_semantic_diff(diff: dict[str, object]) -> str:
    if not diff:
        return "no semantic differences"
    lines = ["semantic differences:"]
    for key, value in diff.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _event_signature(
    trace: ExecutionTrace, acceptability: ReplayAcceptability
) -> list[tuple[object, ...]]:
    if acceptability == ReplayAcceptability.EXACT_MATCH:
        return [
            (event.event_type, event.step_index, event.payload_hash)
            for event in trace.events
        ]
    if acceptability == ReplayAcceptability.INVARIANT_PRESERVING:
        return [(event.event_type, event.step_index) for event in trace.events]
    if acceptability == ReplayAcceptability.STATISTICALLY_BOUNDED:
        return sorted((event.event_type, event.step_index) for event in trace.events)
    return [
        (event.event_type, event.step_index, event.payload_hash)
        for event in trace.events
    ]


__all__ = ["render_semantic_diff", "semantic_trace_diff"]
