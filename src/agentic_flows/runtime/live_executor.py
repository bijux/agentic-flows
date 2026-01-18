# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.agent_executor import AgentExecutor
from agentic_flows.runtime.artifact_store import ArtifactStore
from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.runtime.flow_boundary import enforce_flow_boundary
from agentic_flows.runtime.reasoning_executor import ReasoningExecutor
from agentic_flows.runtime.retrieval_executor import RetrievalExecutor
from agentic_flows.runtime.retrieval_fingerprint import fingerprint_retrieval
from agentic_flows.runtime.time import utc_now_deterministic
from agentic_flows.runtime.trace_recorder import TraceRecorder
from agentic_flows.runtime.verification_engine import VerificationEngine
from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.execution_event import ExecutionEvent
from agentic_flows.spec.execution_trace import ExecutionTrace
from agentic_flows.spec.ids import ContentHash, ResolverID, ToolID
from agentic_flows.spec.ontology import ArtifactType, EventType
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.resolved_flow import ResolvedFlow
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.verification import VerificationPolicy
from agentic_flows.spec.verification_result import VerificationResult


class LiveExecutor:
    def execute(
        self,
        resolved_flow: ResolvedFlow,
        *,
        verification_policy: VerificationPolicy,
        artifact_store: ArtifactStore,
    ) -> tuple[
        ExecutionTrace,
        list[Artifact],
        list[RetrievedEvidence],
        list[ReasoningBundle],
        list[VerificationResult],
    ]:
        plan = resolved_flow.plan
        enforce_flow_boundary(plan)
        recorder = TraceRecorder()
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
                )
            )
            event_index += 1

        artifacts: list[Artifact] = []
        evidence: list[RetrievedEvidence] = []
        reasoning_bundles: list[ReasoningBundle] = []
        verification_results: list[VerificationResult] = []
        agent_executor = AgentExecutor(artifact_store)
        retrieval_executor = RetrievalExecutor()
        reasoning_executor = ReasoningExecutor()
        verification_engine = VerificationEngine()
        policy = verification_policy
        tool_agent = ToolID("bijux-agent.run")
        tool_retrieval = ToolID("bijux-rag.retrieve")
        tool_reasoning = ToolID("bijux-rar.reason")

        for step in plan.steps:
            current_evidence: list[RetrievedEvidence] = []
            record_event(
                EventType.STEP_START,
                step.step_index,
                {
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                },
            )

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

                try:
                    retrieved = retrieval_executor.execute(step.retrieval_request)
                except Exception as exc:
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
                output_fingerprint = fingerprint_inputs(
                    [item.content_hash for item in retrieved]
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
            try:
                step_artifacts = agent_executor.execute_step(
                    step, evidence=current_evidence
                )
                artifacts.extend(step_artifacts)
            except Exception as exc:
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
            record_event(
                EventType.TOOL_CALL_END,
                step.step_index,
                {
                    "tool_id": tool_agent,
                    "input_fingerprint": fingerprint_inputs(tool_input),
                    "output_fingerprint": output_fingerprint,
                },
            )

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

            try:
                bundle = reasoning_executor.execute(
                    agent_outputs=step_artifacts,
                    retrieved_evidence=current_evidence,
                )
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
                    artifact_store.create(
                        spec_version="v1",
                        artifact_id=bundle.bundle_id,
                        artifact_type=ArtifactType.REASONING_BUNDLE,
                        producer="reasoning",
                        parent_artifacts=tuple(
                            artifact.artifact_id for artifact in step_artifacts
                        ),
                        content_hash=bundle_hash,
                    )
                )
            except Exception as exc:
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

            result = verification_engine.verify(bundle, current_evidence, policy)
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
            self._resolver_id_from_metadata(plan.resolution_metadata)
        )
        trace = ExecutionTrace(
            spec_version="v1",
            flow_id=plan.flow_id,
            environment_fingerprint=plan.environment_fingerprint,
            plan_hash=plan.plan_hash,
            resolver_id=resolver_id,
            events=recorder.events(),
            finalized=False,
        )
        trace.finalize()
        return trace, artifacts, evidence, reasoning_bundles, verification_results

    @staticmethod
    def _resolver_id_from_metadata(metadata: tuple[tuple[str, str], ...]) -> str:
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
