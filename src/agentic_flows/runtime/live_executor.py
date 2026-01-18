# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.agent_executor import AgentExecutor
from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.runtime.flow_boundary import enforce_flow_boundary
from agentic_flows.runtime.reasoning_executor import ReasoningExecutor
from agentic_flows.runtime.retrieval_executor import RetrievalExecutor
from agentic_flows.runtime.retrieval_fingerprint import fingerprint_retrieval
from agentic_flows.runtime.time import utc_now_deterministic
from agentic_flows.runtime.trace_recorder import TraceRecorder
from agentic_flows.runtime.verification_engine import VerificationEngine
from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.artifact_types import ArtifactType
from agentic_flows.spec.execution_event import ExecutionEvent
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.execution_trace import ExecutionTrace
from agentic_flows.spec.ids import ContentHash, EventType, ResolverID
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.verification import VerificationPolicy
from agentic_flows.spec.verification_result import VerificationResult


class LiveExecutor:
    def execute(
        self, plan: ExecutionPlan
    ) -> tuple[
        ExecutionTrace,
        list[Artifact],
        list[RetrievedEvidence],
        list[ReasoningBundle],
        list[VerificationResult],
    ]:
        enforce_flow_boundary(plan)
        recorder = TraceRecorder()
        event_index = 0
        artifacts: list[Artifact] = []
        evidence: list[RetrievedEvidence] = []
        reasoning_bundles: list[ReasoningBundle] = []
        verification_results: list[VerificationResult] = []
        agent_executor = AgentExecutor()
        retrieval_executor = RetrievalExecutor()
        reasoning_executor = ReasoningExecutor()
        verification_engine = VerificationEngine()
        policy = VerificationPolicy(
            spec_version="v1",
            verification_level="baseline",
            failure_mode="halt",
            required_evidence=(),
            rules=(),
            fail_on=(),
            escalate_on=(),
        )

        for step in plan.steps:
            current_evidence: list[RetrievedEvidence] = []
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

            if step.retrieval_request is not None:
                retrieval_payload = {
                    "event_type": "RETRIEVAL_START",
                    "step_index": step.step_index,
                    "request_id": step.retrieval_request.request_id,
                    "vector_contract_id": step.retrieval_request.vector_contract_id,
                    "request_fingerprint": fingerprint_retrieval(
                        step.retrieval_request
                    ),
                }
                recorder.record(
                    ExecutionEvent(
                        spec_version="v1",
                        event_index=event_index,
                        step_index=step.step_index,
                        event_type=EventType("RETRIEVAL_START"),
                        timestamp_utc=utc_now_deterministic(event_index),
                        payload_hash=fingerprint_inputs(retrieval_payload),
                    )
                )
                event_index += 1

                try:
                    retrieved = retrieval_executor.execute(step.retrieval_request)
                except Exception as exc:
                    failed_payload = {
                        "event_type": "RETRIEVAL_FAILED",
                        "step_index": step.step_index,
                        "request_id": step.retrieval_request.request_id,
                        "vector_contract_id": step.retrieval_request.vector_contract_id,
                        "error": str(exc),
                    }
                    recorder.record(
                        ExecutionEvent(
                            spec_version="v1",
                            event_index=event_index,
                            step_index=step.step_index,
                            event_type=EventType("RETRIEVAL_FAILED"),
                            timestamp_utc=utc_now_deterministic(event_index),
                            payload_hash=fingerprint_inputs(failed_payload),
                        )
                    )
                    event_index += 1
                    break

                current_evidence = retrieved
                evidence.extend(retrieved)

                retrieval_done_payload = {
                    "event_type": "RETRIEVAL_END",
                    "step_index": step.step_index,
                    "request_id": step.retrieval_request.request_id,
                    "vector_contract_id": step.retrieval_request.vector_contract_id,
                    "evidence_hashes": [item.content_hash for item in retrieved],
                }
                recorder.record(
                    ExecutionEvent(
                        spec_version="v1",
                        event_index=event_index,
                        step_index=step.step_index,
                        event_type=EventType("RETRIEVAL_END"),
                        timestamp_utc=utc_now_deterministic(event_index),
                        payload_hash=fingerprint_inputs(retrieval_done_payload),
                    )
                )
                event_index += 1

            try:
                step_artifacts = agent_executor.execute_step(
                    step, evidence=current_evidence
                )
                artifacts.extend(step_artifacts)
            except Exception as exc:
                failed_payload = {
                    "event_type": "STEP_FAILED",
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                    "error": str(exc),
                }
                recorder.record(
                    ExecutionEvent(
                        spec_version="v1",
                        event_index=event_index,
                        step_index=step.step_index,
                        event_type=EventType("STEP_FAILED"),
                        timestamp_utc=utc_now_deterministic(event_index),
                        payload_hash=fingerprint_inputs(failed_payload),
                    )
                )
                event_index += 1
                break

            reasoning_payload = {
                "event_type": "REASONING_START",
                "step_index": step.step_index,
                "agent_id": step.agent_id,
            }
            recorder.record(
                ExecutionEvent(
                    spec_version="v1",
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type=EventType("REASONING_START"),
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(reasoning_payload),
                )
            )
            event_index += 1

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

                reasoning_done_payload = {
                    "event_type": "REASONING_END",
                    "step_index": step.step_index,
                    "bundle_hash": bundle_hash,
                    "claim_count": len(bundle.claims),
                }
                recorder.record(
                    ExecutionEvent(
                        spec_version="v1",
                        event_index=event_index,
                        step_index=step.step_index,
                        event_type=EventType("REASONING_END"),
                        timestamp_utc=utc_now_deterministic(event_index),
                        payload_hash=fingerprint_inputs(reasoning_done_payload),
                    )
                )
                event_index += 1

                artifacts.append(
                    Artifact(
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
                failed_payload = {
                    "event_type": "REASONING_FAILED",
                    "step_index": step.step_index,
                    "agent_id": step.agent_id,
                    "error": str(exc),
                }
                recorder.record(
                    ExecutionEvent(
                        spec_version="v1",
                        event_index=event_index,
                        step_index=step.step_index,
                        event_type=EventType("REASONING_FAILED"),
                        timestamp_utc=utc_now_deterministic(event_index),
                        payload_hash=fingerprint_inputs(failed_payload),
                    )
                )
                event_index += 1
                break

            verification_payload = {
                "event_type": "VERIFICATION_START",
                "step_index": step.step_index,
            }
            recorder.record(
                ExecutionEvent(
                    spec_version="v1",
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type=EventType("VERIFICATION_START"),
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(verification_payload),
                )
            )
            event_index += 1

            result = verification_engine.verify(bundle, current_evidence, policy)
            verification_results.append(result)
            verification_payload = {
                "event_type": f"VERIFICATION_{result.status}",
                "step_index": step.step_index,
                "status": result.status,
                "rule_ids": result.violations,
            }
            event_type = f"VERIFICATION_{result.status}"
            recorder.record(
                ExecutionEvent(
                    spec_version="v1",
                    event_index=event_index,
                    step_index=step.step_index,
                    event_type=EventType(event_type),
                    timestamp_utc=utc_now_deterministic(event_index),
                    payload_hash=fingerprint_inputs(verification_payload),
                )
            )
            event_index += 1

            if result.status != "PASS":
                break

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
        return trace, artifacts, evidence, reasoning_bundles, verification_results

    @staticmethod
    def _resolver_id_from_metadata(metadata: tuple[tuple[str, str], ...]) -> str:
        for key, value in metadata:
            if key == "resolver_id":
                return value
        raise ValueError("resolution_metadata missing resolver_id")
