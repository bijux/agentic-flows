# INTERNAL — SUBJECT TO CHANGE WITHOUT NOTICE
# INTERNAL API — NOT STABLE
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for runtime/execution/live_executor.py."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import os
import signal

from agentic_flows.core.authority import finalize_trace
from agentic_flows.core.errors import ExecutionFailure, SemanticViolationError
from agentic_flows.runtime.context import ExecutionContext, RunMode
from agentic_flows.runtime.execution.agent_executor import AgentExecutor
from agentic_flows.runtime.execution.reasoning_executor import ReasoningExecutor
from agentic_flows.runtime.execution.retrieval_executor import RetrievalExecutor
from agentic_flows.runtime.execution.step_executor import ExecutionOutcome
from agentic_flows.runtime.observability.fingerprint import (
    fingerprint_inputs,
    fingerprint_policy,
)
from agentic_flows.runtime.observability.flow_invariants import validate_flow_invariants
from agentic_flows.runtime.observability.retrieval_fingerprint import (
    fingerprint_retrieval,
)
from agentic_flows.runtime.observability.time import utc_now_deterministic
from agentic_flows.runtime.orchestration.flow_boundary import enforce_flow_boundary
from agentic_flows.runtime.verification_engine import VerificationOrchestrator
from agentic_flows.spec.contracts.step_contract import validate_outputs
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_arbitration import VerificationArbitration
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology import (
    ArtifactScope,
    ArtifactType,
    CausalityTag,
    StepType,
    VerificationPhase,
    VerificationRandomness,
)
from agentic_flows.spec.ontology.ids import (
    ArtifactID,
    ClaimID,
    ContentHash,
    PolicyFingerprint,
    ResolverID,
    RuleID,
    ToolID,
)
from agentic_flows.spec.ontology.public import EventType


@dataclass
class _PhaseState:
    """Internal helper type; not part of the public API."""

    recorder: object
    event_index: int
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]
    verification_results: list[VerificationResult]
    verification_arbitrations: list[VerificationArbitration]
    tool_invocations: list[ToolInvocation]
    pending_invocations: dict[tuple[int, ToolID], ContentHash]
    interrupted: bool


def _notify_stage(context: ExecutionContext, stage: str, phase: str) -> None:
    """Internal helper; not part of the public API."""
    hook_name = f"on_stage_{phase}"
    for observer in context.observers:
        hook = getattr(observer, hook_name, None)
        if callable(hook):
            hook(stage)


_EVENT_CAUSALITY = {
    EventType.TOOL_CALL_START: CausalityTag.TOOL,
    EventType.TOOL_CALL_END: CausalityTag.TOOL,
    EventType.TOOL_CALL_FAIL: CausalityTag.TOOL,
    EventType.RETRIEVAL_START: CausalityTag.DATASET,
    EventType.RETRIEVAL_END: CausalityTag.DATASET,
    EventType.RETRIEVAL_FAILED: CausalityTag.DATASET,
    EventType.HUMAN_INTERVENTION: CausalityTag.HUMAN,
    EventType.EXECUTION_INTERRUPTED: CausalityTag.ENVIRONMENT,
    EventType.SEMANTIC_VIOLATION: CausalityTag.ENVIRONMENT,
}


def _causality_tag(event_type: EventType) -> CausalityTag:
    """Internal helper; not part of the public API."""
    return _EVENT_CAUSALITY.get(event_type, CausalityTag.AGENT)


class LiveExecutor:
    """Behavioral contract for LiveExecutor."""

    def execute(
        self,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        """Execute execute and enforce its contract."""
        _notify_stage(context, "planning", "start")
        steps_plan = self._planning_phase(plan)
        _notify_stage(context, "planning", "end")
        _notify_stage(context, "execution", "start")
        phase_state = self._execution_phase(steps_plan, context)
        _notify_stage(context, "execution", "end")
        _notify_stage(context, "finalization", "start")
        result = self._finalization_phase(steps_plan, context, phase_state)
        _notify_stage(context, "finalization", "end")
        return result

    @staticmethod
    def _planning_phase(plan: ExecutionPlan):
        """Internal helper; not part of the public API."""
        steps_plan = plan.plan
        enforce_flow_boundary(steps_plan)
        return steps_plan

    def _execution_phase(self, steps_plan, context: ExecutionContext) -> _PhaseState:
        """Internal helper; not part of the public API."""
        recorder = context.trace_recorder
        event_index = context.starting_event_index
        artifacts: list[Artifact] = list(context.initial_artifacts)
        evidence: list[RetrievedEvidence] = list(context.initial_evidence)
        reasoning_bundles: list[ReasoningBundle] = []
        verification_results: list[VerificationResult] = []
        verification_arbitrations: list[VerificationArbitration] = []
        tool_invocations: list[ToolInvocation] = list(context.initial_tool_invocations)
        agent_executor = AgentExecutor()
        retrieval_executor = RetrievalExecutor()
        reasoning_executor = ReasoningExecutor()
        verification_orchestrator = VerificationOrchestrator()
        policy = context.verification_policy
        tool_agent = ToolID("bijux-agent.run")
        tool_retrieval = ToolID("bijux-rag.retrieve")
        tool_reasoning = ToolID("bijux-rar.reason")
        pending_invocations: dict[tuple[int, ToolID], ContentHash] = {}
        interrupted = False

        evidence_index = context.starting_evidence_index
        tool_invocation_index = context.starting_tool_invocation_index
        entropy_index = context.starting_entropy_index
        entropy_checked_index = context.starting_entropy_index

        def record_event(
            event_type: EventType, step_index: int, payload: dict[str, object]
        ) -> None:
            """Execute record_event and enforce its contract."""
            nonlocal event_index
            payload["event_type"] = event_type.value
            event = ExecutionEvent(
                spec_version="v1",
                event_index=event_index,
                step_index=step_index,
                event_type=event_type,
                causality_tag=_causality_tag(event_type),
                timestamp_utc=utc_now_deterministic(event_index),
                payload=payload,
                payload_hash=fingerprint_inputs(payload),
            )
            recorder.record(
                event,
                context.authority,
            )
            if context.execution_store is not None and context.run_id is not None:
                context.execution_store.save_events(
                    run_id=context.run_id,
                    tenant_id=context.tenant_id,
                    events=(event,),
                )
            for observer in context.observers:
                observer.on_event(event)
            with suppress(Exception):
                context.consume_budget(trace_events=1)
            event_index += 1

        def record_tool_invocation(invocation: ToolInvocation) -> None:
            """Execute record_tool_invocation and enforce its contract."""
            nonlocal tool_invocation_index
            tool_invocations.append(invocation)
            if context.execution_store is not None and context.run_id is not None:
                context.execution_store.append_tool_invocations(
                    run_id=context.run_id,
                    tenant_id=context.tenant_id,
                    tool_invocations=(invocation,),
                    starting_index=tool_invocation_index,
                )
            tool_invocation_index += 1

        def record_evidence(items: list[RetrievedEvidence]) -> None:
            """Execute record_evidence and enforce its contract."""
            nonlocal evidence_index
            if not items:
                return
            if context.execution_store is not None and context.run_id is not None:
                context.execution_store.append_evidence(
                    run_id=context.run_id,
                    evidence=items,
                    starting_index=evidence_index,
                )
            evidence_index += len(items)

        def record_artifacts(items: list[Artifact]) -> None:
            """Execute record_artifacts and enforce its contract."""
            if not items:
                return
            if context.execution_store is not None and context.run_id is not None:
                context.execution_store.save_artifacts(
                    run_id=context.run_id, artifacts=items
                )

        def record_claims(claims: tuple[ClaimID, ...]) -> None:
            """Execute record_claims and enforce its contract."""
            if not claims:
                return
            if context.execution_store is not None and context.run_id is not None:
                context.execution_store.append_claim_ids(
                    run_id=context.run_id,
                    tenant_id=context.tenant_id,
                    claim_ids=claims,
                )

        def flush_entropy_usage() -> None:
            """Execute flush_entropy_usage and enforce its contract."""
            nonlocal entropy_index
            if context.execution_store is None or context.run_id is None:
                return
            usage = context.entropy_usage()
            if len(usage) <= entropy_index:
                return
            new_entries = usage[entropy_index:]
            context.execution_store.append_entropy_usage(
                run_id=context.run_id,
                usage=new_entries,
                starting_index=entropy_index,
            )
            entropy_index = len(usage)

        def enforce_entropy_authorization() -> None:
            """Execute enforce_entropy_authorization and enforce its contract."""
            nonlocal entropy_checked_index
            usage = context.entropy_usage()
            if len(usage) <= entropy_checked_index:
                return
            new_entries = usage[entropy_checked_index:]
            entropy_checked_index = len(usage)
            if not context.strict_determinism:
                return
            for entry in new_entries:
                if not entry.nondeterminism_source.authorized:
                    raise SemanticViolationError(
                        "entropy source used without explicit authorization"
                    )

        def save_checkpoint(step_index: int) -> None:
            """Execute save_checkpoint and enforce its contract."""
            if context.execution_store is None or context.run_id is None:
                return
            context.execution_store.save_checkpoint(
                run_id=context.run_id,
                tenant_id=context.tenant_id,
                step_index=step_index,
                event_index=event_index - 1,
            )

        previous_handler = signal.getsignal(signal.SIGINT)

        def _handle_interrupt(_signum, _frame) -> None:
            """Internal helper; not part of the public API."""
            context.cancel()

        signal.signal(signal.SIGINT, _handle_interrupt)
        try:
            interrupted = self._execute_step_phase(
                steps_plan=steps_plan,
                context=context,
                record_event=record_event,
                record_tool_invocation=record_tool_invocation,
                record_evidence=record_evidence,
                record_artifacts=record_artifacts,
                record_claims=record_claims,
                flush_entropy_usage=flush_entropy_usage,
                enforce_entropy_authorization=enforce_entropy_authorization,
                save_checkpoint=save_checkpoint,
                artifacts=artifacts,
                evidence=evidence,
                reasoning_bundles=reasoning_bundles,
                verification_results=verification_results,
                verification_arbitrations=verification_arbitrations,
                tool_invocations=tool_invocations,
                pending_invocations=pending_invocations,
                agent_executor=agent_executor,
                retrieval_executor=retrieval_executor,
                reasoning_executor=reasoning_executor,
                verification_orchestrator=verification_orchestrator,
                policy=policy,
                tool_agent=tool_agent,
                tool_retrieval=tool_retrieval,
                tool_reasoning=tool_reasoning,
            )
        finally:
            signal.signal(signal.SIGINT, previous_handler)

        return _PhaseState(
            recorder=recorder,
            event_index=event_index,
            artifacts=artifacts,
            evidence=evidence,
            reasoning_bundles=reasoning_bundles,
            verification_results=verification_results,
            verification_arbitrations=verification_arbitrations,
            tool_invocations=tool_invocations,
            pending_invocations=pending_invocations,
            interrupted=interrupted,
        )

    def _execute_step_phase(
        self,
        *,
        steps_plan,
        context: ExecutionContext,
        record_event,
        record_tool_invocation,
        record_evidence,
        record_artifacts,
        record_claims,
        flush_entropy_usage,
        enforce_entropy_authorization,
        save_checkpoint,
        artifacts: list[Artifact],
        evidence: list[RetrievedEvidence],
        reasoning_bundles: list[ReasoningBundle],
        verification_results: list[VerificationResult],
        verification_arbitrations: list[VerificationArbitration],
        tool_invocations: list[ToolInvocation],
        pending_invocations: dict[tuple[int, ToolID], ContentHash],
        agent_executor: AgentExecutor,
        retrieval_executor: RetrievalExecutor,
        reasoning_executor: ReasoningExecutor,
        verification_orchestrator: VerificationOrchestrator,
        policy: VerificationPolicy | None,
        tool_agent: ToolID,
        tool_retrieval: ToolID,
        tool_reasoning: ToolID,
    ) -> bool:
        """Internal helper; not part of the public API."""
        interrupted = False
        for step in steps_plan.steps:
            if step.step_index <= context.resume_from_step_index:
                continue
            if context.is_cancelled():
                record_event(
                    EventType.EXECUTION_INTERRUPTED,
                    step.step_index,
                    {"step_index": step.step_index, "reason": "sigint"},
                )
                interrupted = True
                break
            current_evidence: list[RetrievedEvidence] = []
            context.record_evidence(step.step_index, [])
            context.start_step_budget()
            record_event(
                EventType.STEP_START,
                step.step_index,
                {
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                },
            )
            try:
                context.consume_budget(steps=1)
            except Exception as exc:
                record_event(
                    EventType.STEP_FAILED,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "agent_id": step.agent_id,
                        "error": str(exc),
                    },
                )
                break

            if step.retrieval_request is not None:
                request_fingerprint = fingerprint_retrieval(step.retrieval_request)
                record_event(
                    EventType.RETRIEVAL_START,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "request_id": step.retrieval_request.request_id,
                        "vector_contract_id": step.retrieval_request.vector_contract_id,
                        "request_fingerprint": request_fingerprint,
                    },
                )
                tool_input = {
                    "tool_id": tool_retrieval,
                    "request_id": step.retrieval_request.request_id,
                    "vector_contract_id": step.retrieval_request.vector_contract_id,
                    "request_fingerprint": request_fingerprint,
                }
                record_event(
                    EventType.TOOL_CALL_START,
                    step.step_index,
                    {
                        "tool_id": tool_retrieval,
                        "input_fingerprint": fingerprint_inputs(tool_input),
                    },
                )
                pending_invocations[(step.step_index, tool_retrieval)] = ContentHash(
                    fingerprint_inputs(tool_input)
                )

                try:
                    retrieved = retrieval_executor.execute(step, context)
                except Exception as exc:
                    input_fingerprint = pending_invocations.pop(
                        (step.step_index, tool_retrieval),
                        ContentHash(fingerprint_inputs(tool_input)),
                    )
                    record_tool_invocation(
                        ToolInvocation(
                            spec_version="v1",
                            tool_id=tool_retrieval,
                            determinism_level=step.determinism_level,
                            inputs_fingerprint=input_fingerprint,
                            outputs_fingerprint=None,
                            duration=0.0,
                            outcome="fail",
                        )
                    )
                    record_event(
                        EventType.TOOL_CALL_FAIL,
                        step.step_index,
                        {
                            "tool_id": tool_retrieval,
                            "input_fingerprint": fingerprint_inputs(tool_input),
                            "error": str(exc),
                        },
                    )
                    record_event(
                        EventType.RETRIEVAL_FAILED,
                        step.step_index,
                        {
                            "step_index": step.step_index,
                            "request_id": step.retrieval_request.request_id,
                            "vector_contract_id": step.retrieval_request.vector_contract_id,
                            "error": str(exc),
                        },
                    )
                    break

                current_evidence = retrieved
                evidence.extend(retrieved)
                context.record_evidence(step.step_index, current_evidence)
                record_evidence(retrieved)
                enforce_entropy_authorization()
                try:
                    context.consume_budget(artifacts=0)
                    context.consume_evidence_budget(len(retrieved))
                except Exception as exc:
                    record_event(
                        EventType.RETRIEVAL_FAILED,
                        step.step_index,
                        {
                            "step_index": step.step_index,
                            "request_id": step.retrieval_request.request_id,
                            "vector_contract_id": step.retrieval_request.vector_contract_id,
                            "error": str(exc),
                        },
                    )
                    break
                try:
                    for item in retrieved:
                        context.artifact_store.create(
                            spec_version="v1",
                            artifact_id=ArtifactID(
                                f"evidence-{step.step_index}-{item.evidence_id}"
                            ),
                            tenant_id=context.tenant_id,
                            artifact_type=ArtifactType.RETRIEVED_EVIDENCE,
                            producer="retrieval",
                            parent_artifacts=(),
                            content_hash=item.content_hash,
                            scope=ArtifactScope.AUDIT,
                        )
                except Exception as exc:
                    record_event(
                        EventType.RETRIEVAL_FAILED,
                        step.step_index,
                        {
                            "step_index": step.step_index,
                            "request_id": step.retrieval_request.request_id,
                            "vector_contract_id": step.retrieval_request.vector_contract_id,
                            "error": str(exc),
                        },
                    )
                    break

                output_fingerprint = fingerprint_inputs(
                    [
                        {
                            "evidence_id": item.evidence_id,
                            "content_hash": item.content_hash,
                        }
                        for item in retrieved
                    ]
                )
                input_fingerprint = pending_invocations.pop(
                    (step.step_index, tool_retrieval),
                    ContentHash(fingerprint_inputs(tool_input)),
                )
                record_tool_invocation(
                    ToolInvocation(
                        spec_version="v1",
                        tool_id=tool_retrieval,
                        determinism_level=step.determinism_level,
                        inputs_fingerprint=input_fingerprint,
                        outputs_fingerprint=ContentHash(output_fingerprint),
                        duration=0.0,
                        outcome="success",
                    )
                )
                record_event(
                    EventType.TOOL_CALL_END,
                    step.step_index,
                    {
                        "tool_id": tool_retrieval,
                        "input_fingerprint": fingerprint_inputs(tool_input),
                        "output_fingerprint": output_fingerprint,
                    },
                )

                record_event(
                    EventType.RETRIEVAL_END,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "request_id": step.retrieval_request.request_id,
                        "vector_contract_id": step.retrieval_request.vector_contract_id,
                        "evidence_hashes": [item.content_hash for item in retrieved],
                    },
                )

            tool_input = {
                "tool_id": tool_agent,
                "agent_id": step.agent_id,
                "inputs_fingerprint": step.inputs_fingerprint,
                "evidence_ids": [item.evidence_id for item in current_evidence],
            }
            record_event(
                EventType.TOOL_CALL_START,
                step.step_index,
                {
                    "tool_id": tool_agent,
                    "input_fingerprint": fingerprint_inputs(tool_input),
                },
            )
            pending_invocations[(step.step_index, tool_agent)] = ContentHash(
                fingerprint_inputs(tool_input)
            )
            step_artifacts: list[Artifact] = []
            try:
                step_artifacts = agent_executor.execute(step, context)
                artifacts.extend(step_artifacts)
                record_artifacts(step_artifacts)
                validate_outputs(StepType.AGENT, step_artifacts, current_evidence)
                context.consume_budget(artifacts=len(step_artifacts))
                context.consume_step_artifacts(len(step_artifacts))
            except Exception as exc:
                input_fingerprint = pending_invocations.pop(
                    (step.step_index, tool_agent),
                    ContentHash(fingerprint_inputs(tool_input)),
                )
                record_tool_invocation(
                    ToolInvocation(
                        spec_version="v1",
                        tool_id=tool_agent,
                        determinism_level=step.determinism_level,
                        inputs_fingerprint=input_fingerprint,
                        outputs_fingerprint=None,
                        duration=0.0,
                        outcome="fail",
                    )
                )
                record_event(
                    EventType.TOOL_CALL_FAIL,
                    step.step_index,
                    {
                        "tool_id": tool_agent,
                        "input_fingerprint": fingerprint_inputs(tool_input),
                        "error": str(exc),
                    },
                )
                record_event(
                    EventType.STEP_FAILED,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "agent_id": step.agent_id,
                        "error": str(exc),
                    },
                )
                break

            output_fingerprint = fingerprint_inputs(
                [
                    {
                        "artifact_id": item.artifact_id,
                        "content_hash": item.content_hash,
                    }
                    for item in step_artifacts
                ]
            )
            input_fingerprint = pending_invocations.pop(
                (step.step_index, tool_agent),
                ContentHash(fingerprint_inputs(tool_input)),
            )
            record_tool_invocation(
                ToolInvocation(
                    spec_version="v1",
                    tool_id=tool_agent,
                    determinism_level=step.determinism_level,
                    inputs_fingerprint=input_fingerprint,
                    outputs_fingerprint=ContentHash(output_fingerprint),
                    duration=0.0,
                    outcome="success",
                )
            )
            record_event(
                EventType.TOOL_CALL_END,
                step.step_index,
                {
                    "tool_id": tool_agent,
                    "input_fingerprint": fingerprint_inputs(tool_input),
                    "output_fingerprint": output_fingerprint,
                },
            )

            if str(step.agent_id) == "force-partial-failure":
                verification_results.append(
                    VerificationResult(
                        spec_version="v1",
                        engine_id="forced",
                        status="FAIL",
                        reason="forced_partial_failure",
                        randomness=VerificationRandomness.DETERMINISTIC,
                        violations=(RuleID("forced_partial_failure"),),
                        checked_artifact_ids=tuple(
                            artifact.artifact_id for artifact in step_artifacts
                        ),
                        phase=VerificationPhase.POST_EXECUTION,
                        rules_applied=(),
                        decision="FAIL",
                    )
                )
                record_event(
                    EventType.VERIFICATION_FAIL,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "status": "FAIL",
                        "rule_ids": ["forced_partial_failure"],
                    },
                )
                record_event(
                    EventType.STEP_FAILED,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "agent_id": step.agent_id,
                        "error": "forced_partial_failure",
                    },
                )
                if context.mode == RunMode.UNSAFE:
                    record_event(
                        EventType.SEMANTIC_VIOLATION,
                        step.step_index,
                        {
                            "step_index": step.step_index,
                            "decision": "FAIL",
                            "rule_ids": ["forced_partial_failure"],
                        },
                    )
                    continue
                break

            record_event(
                EventType.REASONING_START,
                step.step_index,
                {
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                },
            )
            tool_input = {
                "tool_id": tool_reasoning,
                "agent_id": step.agent_id,
                "artifact_ids": [artifact.artifact_id for artifact in step_artifacts],
                "evidence_ids": [item.evidence_id for item in current_evidence],
            }
            record_event(
                EventType.TOOL_CALL_START,
                step.step_index,
                {
                    "tool_id": tool_reasoning,
                    "input_fingerprint": fingerprint_inputs(tool_input),
                },
            )
            pending_invocations[(step.step_index, tool_reasoning)] = ContentHash(
                fingerprint_inputs(tool_input)
            )

            try:
                bundle = reasoning_executor.execute(step, context)
                reasoning_bundles.append(bundle)
                bundle_hash = ContentHash(reasoning_executor.bundle_hash(bundle))

                evidence_ids = {item.evidence_id for item in current_evidence}
                for claim in bundle.claims:
                    if any(
                        evidence_id not in evidence_ids
                        for evidence_id in claim.supported_by
                    ):
                        raise ValueError("reasoning claim references unknown evidence")

                record_event(
                    EventType.TOOL_CALL_END,
                    step.step_index,
                    {
                        "tool_id": tool_reasoning,
                        "input_fingerprint": fingerprint_inputs(tool_input),
                        "output_fingerprint": fingerprint_inputs(
                            {"bundle_hash": bundle_hash}
                        ),
                    },
                )
                input_fingerprint = pending_invocations.pop(
                    (step.step_index, tool_reasoning),
                    ContentHash(fingerprint_inputs(tool_input)),
                )
                record_tool_invocation(
                    ToolInvocation(
                        spec_version="v1",
                        tool_id=tool_reasoning,
                        determinism_level=step.determinism_level,
                        inputs_fingerprint=input_fingerprint,
                        outputs_fingerprint=ContentHash(
                            fingerprint_inputs({"bundle_hash": bundle_hash})
                        ),
                        duration=0.0,
                        outcome="success",
                    )
                )
                record_event(
                    EventType.REASONING_END,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "bundle_hash": bundle_hash,
                        "claim_count": len(bundle.claims),
                    },
                )
                record_claims(tuple(claim.claim_id for claim in bundle.claims))

                artifacts.append(
                    context.artifact_store.create(
                        spec_version="v1",
                        artifact_id=bundle.bundle_id,
                        tenant_id=context.tenant_id,
                        artifact_type=ArtifactType.REASONING_BUNDLE,
                        producer="reasoning",
                        parent_artifacts=tuple(
                            artifact.artifact_id for artifact in step_artifacts
                        ),
                        content_hash=bundle_hash,
                        scope=ArtifactScope.AUDIT,
                    )
                )
                record_artifacts([artifacts[-1]])
                context.consume_budget(
                    artifacts=1,
                    tokens=sum(len(claim.statement.split()) for claim in bundle.claims),
                )
                context.consume_step_artifacts(1)
                validate_outputs(
                    StepType.REASONING,
                    [artifacts[-1]],
                    current_evidence,
                )
            except Exception as exc:
                input_fingerprint = pending_invocations.pop(
                    (step.step_index, tool_reasoning),
                    ContentHash(fingerprint_inputs(tool_input)),
                )
                record_tool_invocation(
                    ToolInvocation(
                        spec_version="v1",
                        tool_id=tool_reasoning,
                        determinism_level=step.determinism_level,
                        inputs_fingerprint=input_fingerprint,
                        outputs_fingerprint=None,
                        duration=0.0,
                        outcome="fail",
                    )
                )
                record_event(
                    EventType.TOOL_CALL_FAIL,
                    step.step_index,
                    {
                        "tool_id": tool_reasoning,
                        "input_fingerprint": fingerprint_inputs(tool_input),
                        "error": str(exc),
                    },
                )
                record_event(
                    EventType.REASONING_FAILED,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "agent_id": step.agent_id,
                        "error": str(exc),
                    },
                )
                break

            record_event(
                EventType.VERIFICATION_START,
                step.step_index,
                {"step_index": step.step_index},
            )

            try:
                stored_artifacts = [
                    context.artifact_store.load(
                        item.artifact_id, tenant_id=context.tenant_id
                    )
                    for item in step_artifacts
                ]
            except Exception as exc:
                verification_results.append(
                    VerificationResult(
                        spec_version="v1",
                        engine_id="integrity",
                        status="FAIL",
                        reason="artifact_store_integrity",
                        randomness=VerificationRandomness.DETERMINISTIC,
                        violations=(RuleID("artifact_store_integrity"),),
                        checked_artifact_ids=tuple(
                            artifact.artifact_id for artifact in step_artifacts
                        ),
                        phase=VerificationPhase.POST_EXECUTION,
                        rules_applied=(),
                        decision="FAIL",
                    )
                )
                record_event(
                    EventType.VERIFICATION_FAIL,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "status": "FAIL",
                        "rule_ids": ["artifact_store_integrity"],
                        "error": str(exc),
                    },
                )
                record_event(
                    EventType.STEP_FAILED,
                    step.step_index,
                    {
                        "step_index": step.step_index,
                        "agent_id": step.agent_id,
                        "error": str(exc),
                    },
                )
                break

            results, arbitration = verification_orchestrator.verify_bundle(
                bundle, current_evidence, stored_artifacts, policy
            )
            verification_results.extend(results)
            verification_arbitrations.append(arbitration)
            status_to_event = {
                "PASS": EventType.VERIFICATION_PASS,
                "FAIL": EventType.VERIFICATION_FAIL,
                "ESCALATE": EventType.VERIFICATION_ESCALATE,
            }
            record_event(
                status_to_event[arbitration.decision],
                step.step_index,
                {
                    "step_index": step.step_index,
                    "status": arbitration.decision,
                    "rule_ids": [
                        violation
                        for result in results
                        for violation in result.violations
                    ],
                },
            )
            record_event(
                EventType.VERIFICATION_ARBITRATION,
                step.step_index,
                {
                    "step_index": step.step_index,
                    "decision": arbitration.decision,
                    "engine_ids": arbitration.engine_ids,
                    "engine_statuses": arbitration.engine_statuses,
                },
            )

            if arbitration.decision != "PASS":
                if context.mode == RunMode.UNSAFE:
                    record_event(
                        EventType.SEMANTIC_VIOLATION,
                        step.step_index,
                        {
                            "step_index": step.step_index,
                            "decision": arbitration.decision,
                            "rule_ids": [
                                violation
                                for result in results
                                for violation in result.violations
                            ],
                        },
                    )
                else:
                    break

            record_event(
                EventType.STEP_END,
                step.step_index,
                {
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                },
            )
            enforce_entropy_authorization()
            flush_entropy_usage()
            save_checkpoint(step.step_index)
            crash_step = os.environ.get("AF_CRASH_AT_STEP")
            if crash_step is not None and int(crash_step) == step.step_index:
                os.kill(os.getpid(), signal.SIGKILL)

        if not interrupted and policy is not None and reasoning_bundles:
            flow_results, flow_arbitration = verification_orchestrator.verify_flow(
                reasoning_bundles, policy
            )
            verification_results.extend(flow_results)
            verification_arbitrations.append(flow_arbitration)
            record_event(
                EventType.VERIFICATION_ARBITRATION,
                steps_plan.steps[-1].step_index if steps_plan.steps else 0,
                {
                    "step_index": steps_plan.steps[-1].step_index
                    if steps_plan.steps
                    else 0,
                    "decision": flow_arbitration.decision,
                    "engine_ids": flow_arbitration.engine_ids,
                    "engine_statuses": flow_arbitration.engine_statuses,
                },
            )
        return interrupted

    def _finalization_phase(
        self,
        steps_plan,
        context: ExecutionContext,
        state: _PhaseState,
    ) -> ExecutionOutcome:
        """Internal helper; not part of the public API."""
        if state.interrupted:
            raise ExecutionFailure("execution interrupted")

        validate_flow_invariants(context, state.artifacts)

        resolver_id = ResolverID(
            self._resolver_id_from_metadata(steps_plan.resolution_metadata)
        )
        claim_ids = list(context.initial_claim_ids)
        claim_ids.extend(
            claim.claim_id
            for bundle in state.reasoning_bundles
            for claim in bundle.claims
        )
        contradiction_count = sum(
            1
            for result in state.verification_results
            if result.engine_id == "contradiction" and result.status == "FAIL"
        )
        arbitration_decision = (
            state.verification_arbitrations[-1].decision
            if state.verification_arbitrations
            else "none"
        )
        trace = ExecutionTrace(
            spec_version="v1",
            flow_id=steps_plan.flow_id,
            tenant_id=steps_plan.tenant_id,
            parent_flow_id=context.parent_flow_id,
            child_flow_ids=context.child_flow_ids,
            flow_state=steps_plan.flow_state,
            determinism_level=steps_plan.determinism_level,
            replay_acceptability=steps_plan.replay_acceptability,
            dataset=steps_plan.dataset,
            replay_envelope=steps_plan.replay_envelope,
            allow_deprecated_datasets=steps_plan.allow_deprecated_datasets,
            environment_fingerprint=steps_plan.environment_fingerprint,
            plan_hash=steps_plan.plan_hash,
            verification_policy_fingerprint=(
                PolicyFingerprint(fingerprint_policy(context.verification_policy))
                if context.verification_policy is not None
                else None
            ),
            resolver_id=resolver_id,
            events=state.recorder.events(),
            tool_invocations=tuple(state.tool_invocations),
            entropy_usage=context.entropy_usage(),
            claim_ids=tuple(dict.fromkeys(claim_ids)),
            contradiction_count=contradiction_count,
            arbitration_decision=arbitration_decision,
            finalized=False,
        )
        finalize_trace(trace)
        return ExecutionOutcome(
            trace=trace,
            artifacts=state.artifacts,
            evidence=state.evidence,
            reasoning_bundles=state.reasoning_bundles,
            verification_results=state.verification_results,
            verification_arbitrations=state.verification_arbitrations,
        )

    @staticmethod
    def _resolver_id_from_metadata(metadata: tuple[tuple[str, str], ...]) -> str:
        """Internal helper; not part of the public API."""
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
