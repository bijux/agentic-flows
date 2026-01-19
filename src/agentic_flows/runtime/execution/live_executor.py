# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.core.authority import finalize_trace
from agentic_flows.runtime.context import ExecutionContext
from agentic_flows.runtime.execution.step_executor import ExecutionOutcome
from agentic_flows.runtime.observability.fingerprint import fingerprint_inputs
from agentic_flows.runtime.observability.retrieval_fingerprint import (
    fingerprint_retrieval,
)
from agentic_flows.runtime.observability.time import utc_now_deterministic
from agentic_flows.runtime.orchestration.flow_boundary import enforce_flow_boundary
from agentic_flows.runtime.registry import build_step_registry
from agentic_flows.runtime.verification_engine import VerificationEngine
from agentic_flows.spec.contracts.step_contract import validate_outputs
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import ContentHash, ResolverID, RuleID, ToolID
from agentic_flows.spec.ontology.ontology import (
    ArtifactScope,
    ArtifactType,
    EventType,
    StepType,
    VerificationPhase,
)


class LiveExecutor:
    def execute(
        self,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        steps_plan = plan.plan
        enforce_flow_boundary(steps_plan)
        recorder = context.trace_recorder
        event_index = 0

        def record_event(
            event_type: EventType, step_index: int, payload: dict[str, object]
        ) -> None:
            nonlocal event_index
            payload["event_type"] = event_type.value
            recorder.record(
                ExecutionEvent(
                    spec_version="v1",
                    event_index=event_index,
                    step_index=step_index,
                    event_type=event_type,
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(payload),
                ),
                context.authority,
            )
            event_index += 1

        artifacts: list[Artifact] = []
        evidence: list[RetrievedEvidence] = []
        reasoning_bundles: list[ReasoningBundle] = []
        verification_results: list[VerificationResult] = []
        tool_invocations: list[ToolInvocation] = []
        registry = build_step_registry()
        agent_executor = registry[StepType.AGENT]
        retrieval_executor = registry[StepType.RETRIEVAL]
        reasoning_executor = registry[StepType.REASONING]
        verification_engine = VerificationEngine()
        policy = context.verification_policy
        tool_agent = ToolID("bijux-agent.run")
        tool_retrieval = ToolID("bijux-rag.retrieve")
        tool_reasoning = ToolID("bijux-rar.reason")

        pending_invocations: dict[tuple[int, ToolID], ContentHash] = {}

        for step in steps_plan.steps:
            current_evidence: list[RetrievedEvidence] = []
            context.record_evidence(step.step_index, [])
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
                validate_outputs(StepType.RETRIEVAL, (), current_evidence)
                output_fingerprint = fingerprint_inputs(
                    [item.content_hash for item in retrieved]
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
            try:
                step_artifacts = agent_executor.execute(step, context)
                artifacts.extend(step_artifacts)
                validate_outputs(StepType.AGENT, step_artifacts, current_evidence)
                context.consume_budget(artifacts=len(step_artifacts))
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
                    {"artifact_id": item.artifact_id, "content_hash": item.content_hash}
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
                    tokens=sum(len(claim.statement.split()) for claim in bundle.claims),
                )
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

            result = verification_engine.verify(
                bundle, current_evidence, stored_artifacts, policy
            )
            verification_results.append(result)
            status_to_event = {
                "PASS": EventType.VERIFICATION_PASS,
                "FAIL": EventType.VERIFICATION_FAIL,
                "ESCALATE": EventType.VERIFICATION_ESCALATE,
            }
            record_event(
                status_to_event[result.status],
                step.step_index,
                {
                    "step_index": step.step_index,
                    "status": result.status,
                    "rule_ids": result.violations,
                },
            )

            if result.status != "PASS":
                break

            record_event(
                EventType.STEP_END,
                step.step_index,
                {
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                },
            )

        resolver_id = ResolverID(
            self._resolver_id_from_metadata(steps_plan.resolution_metadata)
        )
        trace = ExecutionTrace(
            spec_version="v1",
            flow_id=steps_plan.flow_id,
            environment_fingerprint=steps_plan.environment_fingerprint,
            plan_hash=steps_plan.plan_hash,
            resolver_id=resolver_id,
            events=recorder.events(),
            tool_invocations=tuple(tool_invocations),
            finalized=False,
        )
        finalize_trace(trace)
        return ExecutionOutcome(
            trace=trace,
            artifacts=artifacts,
            evidence=evidence,
            reasoning_bundles=reasoning_bundles,
            verification_results=verification_results,
        )

    @staticmethod
    def _resolver_id_from_metadata(metadata: tuple[tuple[str, str], ...]) -> str:
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
