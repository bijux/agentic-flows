# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import signal

from agentic_flows.core.authority import finalize_trace
from agentic_flows.core.errors import ExecutionFailure
from agentic_flows.runtime.context import ExecutionContext, RunMode
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
from agentic_flows.runtime.registry import build_step_registry
from agentic_flows.runtime.verification_engine import VerificationOrchestrator
from agentic_flows.spec.contracts.step_contract import validate_outputs
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.model.verification_arbitration import VerificationArbitration
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import (
    ArtifactID,
    ContentHash,
    PolicyFingerprint,
    ResolverID,
    RuleID,
    ToolID,
)
from agentic_flows.spec.ontology.ontology import (
    ArtifactScope,
    ArtifactType,
    EventType,
    StepType,
    VerificationPhase,
)


@dataclass
class _PhaseState:
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


class LiveExecutor:
    def execute(
        self,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        steps_plan = self._planning_phase(plan)
        state = self._execution_phase(steps_plan, context)
        return self._finalization_phase(steps_plan, context, state)

    @staticmethod
    def _planning_phase(plan: ExecutionPlan):
        steps_plan = plan.plan
        enforce_flow_boundary(steps_plan)
        return steps_plan

    def _execution_phase(self, steps_plan, context: ExecutionContext) -> _PhaseState:
        recorder = context.trace_recorder
        event_index = 0
        artifacts: list[Artifact] = []
        evidence: list[RetrievedEvidence] = []
        reasoning_bundles: list[ReasoningBundle] = []
        verification_results: list[VerificationResult] = []
        verification_arbitrations: list[VerificationArbitration] = []
        tool_invocations: list[ToolInvocation] = []
        registry = build_step_registry()
        agent_executor = registry[StepType.AGENT]
        retrieval_executor = registry[StepType.RETRIEVAL]
        reasoning_executor = registry[StepType.REASONING]
        verification_orchestrator = VerificationOrchestrator()
        policy = context.verification_policy
        tool_agent = ToolID("bijux-agent.run")
        tool_retrieval = ToolID("bijux-rag.retrieve")
        tool_reasoning = ToolID("bijux-rar.reason")
        pending_invocations: dict[tuple[int, ToolID], ContentHash] = {}
        interrupted = False

        def record_event(
            event_type: EventType, step_index: int, payload: dict[str, object]
        ) -> None:
            nonlocal event_index
            payload["event_type"] = event_type.value
            event = ExecutionEvent(
                spec_version="v1",
                event_index=event_index,
                step_index=step_index,
                event_type=event_type,
                timestamp_utc=utc_now_deterministic(event_index),
                payload=payload,
                payload_hash=fingerprint_inputs(payload),
            )
            recorder.record(
                event,
                context.authority,
            )
            for observer in context.observers:
                observer.on_event(event)
            with suppress(Exception):
                context.consume_budget(trace_events=1)
            event_index += 1

        previous_handler = signal.getsignal(signal.SIGINT)

        def _handle_interrupt(_signum, _frame) -> None:
            context.cancel()

        signal.signal(signal.SIGINT, _handle_interrupt)
        try:
            for step in steps_plan.steps:
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
                    pending_invocations[(step.step_index, tool_retrieval)] = (
                        ContentHash(fingerprint_inputs(tool_input))
                    )

                    try:
                        retrieved = retrieval_executor.execute(step, context)
                    except Exception as exc:
                        input_fingerprint = pending_invocations.pop(
                            (step.step_index, tool_retrieval),
                            ContentHash(fingerprint_inputs(tool_input)),
                        )
                        tool_invocations.append(
                            ToolInvocation(
                                spec_version="v1",
                                tool_id=tool_retrieval,
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
                    tool_invocations.append(
                        ToolInvocation(
                            spec_version="v1",
                            tool_id=tool_retrieval,
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
                            "evidence_hashes": [
                                item.content_hash for item in retrieved
                            ],
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
                    validate_outputs(StepType.AGENT, step_artifacts, current_evidence)
                    context.consume_budget(artifacts=len(step_artifacts))
                    context.consume_step_artifacts(len(step_artifacts))
                except Exception as exc:
                    input_fingerprint = pending_invocations.pop(
                        (step.step_index, tool_agent),
                        ContentHash(fingerprint_inputs(tool_input)),
                    )
                    tool_invocations.append(
                        ToolInvocation(
                            spec_version="v1",
                            tool_id=tool_agent,
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
                tool_invocations.append(
                    ToolInvocation(
                        spec_version="v1",
                        tool_id=tool_agent,
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
                    "artifact_ids": [
                        artifact.artifact_id for artifact in step_artifacts
                    ],
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
                            raise ValueError(
                                "reasoning claim references unknown evidence"
                            )

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
                    tool_invocations.append(
                        ToolInvocation(
                            spec_version="v1",
                            tool_id=tool_reasoning,
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

                    artifacts.append(
                        context.artifact_store.create(
                            spec_version="v1",
                            artifact_id=bundle.bundle_id,
                            artifact_type=ArtifactType.REASONING_BUNDLE,
                            producer="reasoning",
                            parent_artifacts=tuple(
                                artifact.artifact_id for artifact in step_artifacts
                            ),
                            content_hash=bundle_hash,
                            scope=ArtifactScope.AUDIT,
                        )
                    )
                    context.consume_budget(
                        artifacts=1,
                        tokens=sum(
                            len(claim.statement.split()) for claim in bundle.claims
                        ),
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
                    tool_invocations.append(
                        ToolInvocation(
                            spec_version="v1",
                            tool_id=tool_reasoning,
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
                        context.artifact_store.load(item.artifact_id)
                        for item in step_artifacts
                    ]
                except Exception as exc:
                    verification_results.append(
                        VerificationResult(
                            spec_version="v1",
                            engine_id="integrity",
                            status="FAIL",
                            reason="artifact_store_integrity",
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

    def _finalization_phase(
        self,
        steps_plan,
        context: ExecutionContext,
        state: _PhaseState,
    ) -> ExecutionOutcome:
        if state.interrupted:
            raise ExecutionFailure("execution interrupted")

        validate_flow_invariants(context, state.artifacts)

        resolver_id = ResolverID(
            self._resolver_id_from_metadata(steps_plan.resolution_metadata)
        )
        trace = ExecutionTrace(
            spec_version="v1",
            flow_id=steps_plan.flow_id,
            parent_flow_id=context.parent_flow_id,
            child_flow_ids=context.child_flow_ids,
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
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
