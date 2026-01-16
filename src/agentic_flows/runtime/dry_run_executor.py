# Dry-run exists to generate deterministic audit traces without invoking any agent logic.
# It must remain intelligence-free: no tools, no network, no retrieval, no reasoning code.
# Forbidden: calling bijux-agent, bijux-rag, bijux-rar, bijux-vex, or any external side effects.
from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.runtime.time import utc_now_deterministic
from agentic_flows.runtime.trace_recorder import TraceRecorder
from agentic_flows.spec.execution_event import ExecutionEvent
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.execution_trace import ExecutionTrace


class DryRunExecutor:
    def execute(self, plan: ExecutionPlan) -> ExecutionTrace:
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
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type="STEP_START",
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
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type="STEP_END",
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(end_payload),
                )
            )
            event_index += 1

        resolver_id = self._resolver_id_from_metadata(plan.resolution_metadata)
        return ExecutionTrace(
            flow_id=plan.flow_id,
            environment_fingerprint=plan.environment_fingerprint,
            resolver_id=resolver_id,
            events=recorder.events(),
        )

    @staticmethod
    def _resolver_id_from_metadata(metadata: tuple[tuple[str, str], ...]) -> str:
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
