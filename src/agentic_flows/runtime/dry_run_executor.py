# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

# Dry-run exists to generate repeatable traces when inputs are fixed, without invoking any agent logic.
# It must remain intelligence-free: no tools, no network, no retrieval, no reasoning code.
# Forbidden: calling bijux-agent, bijux-rag, bijux-rar, bijux-vex, or any external side effects.
from __future__ import annotations

from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.runtime.flow_boundary import enforce_flow_boundary
from agentic_flows.runtime.time import utc_now_deterministic
from agentic_flows.runtime.trace_recorder import TraceRecorder
from agentic_flows.spec.execution_event import ExecutionEvent
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.execution_trace import ExecutionTrace
from agentic_flows.spec.ids import EventType, ResolverID


class DryRunExecutor:
    def execute(self, plan: ExecutionPlan) -> ExecutionTrace:
        enforce_flow_boundary(plan)
        recorder = TraceRecorder()
        event_index = 0

        for step in plan.steps:
            start_payload = {
                "event_type": "STEP_START",
                "step_index": step.step_index,
                "agent_id": step.agent_id,
            }
            recorder.record(
                ExecutionEvent(
                    spec_version="v1",
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type=EventType("STEP_START"),
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(start_payload),
                )
            )
            event_index += 1

            end_payload = {
                "event_type": "STEP_END",
                "step_index": step.step_index,
                "agent_id": step.agent_id,
            }
            recorder.record(
                ExecutionEvent(
                    spec_version="v1",
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type=EventType("STEP_END"),
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(end_payload),
                )
            )
            event_index += 1

        resolver_id = ResolverID(
            self._resolver_id_from_metadata(plan.resolution_metadata)
        )
        trace = ExecutionTrace(
            spec_version="v1",
            flow_id=plan.flow_id,
            environment_fingerprint=plan.environment_fingerprint,
            resolver_id=resolver_id,
            events=recorder.events(),
            finalized=False,
        )
        trace.finalize()
        return trace

    @staticmethod
    def _resolver_id_from_metadata(metadata: tuple[tuple[str, str], ...]) -> str:
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
