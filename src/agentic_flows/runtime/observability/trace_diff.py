# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.spec.model.execution_trace import ExecutionTrace


def semantic_trace_diff(
    expected: ExecutionTrace, observed: ExecutionTrace
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
    expected_events = [
        (event.event_type, event.step_index, event.payload_hash)
        for event in expected.events
    ]
    observed_events = [
        (event.event_type, event.step_index, event.payload_hash)
        for event in observed.events
    ]
    if expected_events != observed_events:
        diffs["events"] = {
            "expected": expected_events,
            "observed": observed_events,
        }
    return diffs


def render_semantic_diff(diff: dict[str, object]) -> str:
    if not diff:
        return "no semantic differences"
    lines = ["semantic differences:"]
    for key, value in diff.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


__all__ = ["render_semantic_diff", "semantic_trace_diff"]
