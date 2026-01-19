# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.core.authority import authority_token, enforce_runtime_semantics
from agentic_flows.runtime.artifact_store import ArtifactStore, InMemoryArtifactStore
from agentic_flows.runtime.budget import BudgetState, ExecutionBudget
from agentic_flows.runtime.context import ExecutionContext, RunMode
from agentic_flows.runtime.execution.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.execution.live_executor import LiveExecutor
from agentic_flows.runtime.execution.observer_executor import ObserverExecutor
from agentic_flows.runtime.observability.entropy import EntropyLedger
from agentic_flows.runtime.observability.execution_store import (
    DuckDBExecutionReadStore,
    DuckDBExecutionWriteStore,
)
from agentic_flows.runtime.observability.execution_store_protocol import (
    ExecutionReadStoreProtocol,
    ExecutionWriteStoreProtocol,
)
from agentic_flows.runtime.observability.hooks import RuntimeObserver
from agentic_flows.runtime.observability.observed_run import ObservedRun
from agentic_flows.runtime.observability.trace_recorder import TraceRecorder
from agentic_flows.runtime.orchestration.planner import ExecutionPlanner
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_arbitration import VerificationArbitration
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import ClaimID, FlowID, RunID, TenantID


@dataclass(frozen=True)
class FlowRunResult:
    resolved_flow: ExecutionPlan
    trace: ExecutionTrace | None
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]
    verification_results: list[VerificationResult]
    verification_arbitrations: list[VerificationArbitration]
    run_id: RunID | None = None


@dataclass(frozen=True)
class ExecutionConfig:
    mode: RunMode
    verification_policy: VerificationPolicy | None = None
    artifact_store: ArtifactStore | None = None
    execution_store: ExecutionWriteStoreProtocol | None = None
    execution_read_store: ExecutionReadStoreProtocol | None = None
    budget: ExecutionBudget | None = None
    observed_run: ObservedRun | None = None
    parent_flow_id: FlowID | None = None
    child_flow_ids: tuple[FlowID, ...] | None = None
    observers: tuple[RuntimeObserver, ...] | None = None
    resume_run_id: RunID | None = None

    @classmethod
    def from_command(cls, command: str) -> ExecutionConfig:
        if command == "plan":
            return cls(mode=RunMode.PLAN)
        if command == "dry-run":
            return cls(mode=RunMode.DRY_RUN)
        if command == "run":
            return cls(mode=RunMode.LIVE)
        if command == "observe":
            return cls(mode=RunMode.OBSERVE)
        if command == "unsafe-run":
            return cls(mode=RunMode.UNSAFE)
        raise ValueError(f"Unsupported command: {command}")


@dataclass(frozen=True)
class ResumeState:
    resume_from_step_index: int
    starting_event_index: int
    starting_evidence_index: int
    starting_tool_invocation_index: int
    starting_entropy_index: int
    events: tuple[ExecutionEvent, ...]
    artifacts: tuple[Artifact, ...]
    evidence: tuple[RetrievedEvidence, ...]
    tool_invocations: tuple[ToolInvocation, ...]
    entropy_usage: tuple[EntropyUsage, ...]
    claim_ids: tuple[ClaimID, ...]


def execute_flow(
    manifest: FlowManifest | None = None,
    *,
    resolved_flow: ExecutionPlan | None = None,
    config: ExecutionConfig | None = None,
) -> FlowRunResult:
    execution_config = config or ExecutionConfig(mode=RunMode.LIVE)
    if (manifest is None) == (resolved_flow is None):
        raise ValueError("Provide exactly one of manifest or resolved_flow")
    if resolved_flow is None:
        resolved_flow = ExecutionPlanner().resolve(manifest)

    if execution_config.mode == RunMode.PLAN:
        return FlowRunResult(
            resolved_flow=resolved_flow,
            trace=None,
            artifacts=[],
            evidence=[],
            reasoning_bundles=[],
            verification_results=[],
            verification_arbitrations=[],
            run_id=None,
        )
    if execution_config.execution_store is None:
        raise ValueError("execution_store is required before execution")

    if (
        execution_config.mode in {RunMode.LIVE, RunMode.OBSERVE, RunMode.UNSAFE}
        and execution_config.verification_policy is None
    ):
        raise ValueError("verification_policy is required before execution")

    strategy = LiveExecutor()
    if execution_config.mode == RunMode.DRY_RUN:
        strategy = DryRunExecutor()
    if execution_config.mode == RunMode.OBSERVE:
        strategy = ObserverExecutor()

    store = execution_config.artifact_store or InMemoryArtifactStore()
    run_id = execution_config.resume_run_id
    resume_from_step_index = -1
    starting_event_index = 0
    starting_evidence_index = 0
    starting_tool_invocation_index = 0
    starting_entropy_index = 0
    initial_claim_ids = ()
    initial_artifacts: list[Artifact] = []
    initial_evidence: list[RetrievedEvidence] = []
    initial_tool_invocations: list[ToolInvocation] = []
    trace_recorder = TraceRecorder()
    entropy_ledger = EntropyLedger(resolved_flow.manifest.entropy_budget)
    if run_id is not None:
        read_store = _resolve_read_store(execution_config)
        resume_state = _load_resume_state(
            read_store, run_id=run_id, tenant_id=resolved_flow.manifest.tenant_id
        )
        resume_from_step_index = resume_state.resume_from_step_index
        starting_event_index = resume_state.starting_event_index
        starting_evidence_index = resume_state.starting_evidence_index
        starting_tool_invocation_index = resume_state.starting_tool_invocation_index
        starting_entropy_index = resume_state.starting_entropy_index
        initial_claim_ids = resume_state.claim_ids
        initial_artifacts = list(resume_state.artifacts)
        initial_evidence = list(resume_state.evidence)
        initial_tool_invocations = list(resume_state.tool_invocations)
        trace_recorder = TraceRecorder(resume_state.events)
        entropy_ledger.seed(resume_state.entropy_usage)
    if run_id is None:
        execution_config.execution_store.register_dataset(resolved_flow.plan.dataset)
        run_id = execution_config.execution_store.begin_run(
            plan=resolved_flow.plan, mode=execution_config.mode
        )
        execution_config.execution_store.save_steps(
            run_id=run_id,
            tenant_id=resolved_flow.plan.tenant_id,
            plan=resolved_flow.plan,
        )
    seed = _derive_seed_token(resolved_flow.plan)
    context = ExecutionContext(
        authority=authority_token(),
        seed=seed,
        environment_fingerprint=resolved_flow.plan.environment_fingerprint,
        parent_flow_id=execution_config.parent_flow_id,
        child_flow_ids=execution_config.child_flow_ids or (),
        tenant_id=resolved_flow.manifest.tenant_id,
        artifact_store=store,
        trace_recorder=trace_recorder,
        mode=execution_config.mode,
        verification_policy=execution_config.verification_policy,
        observers=execution_config.observers or (),
        budget=BudgetState(execution_config.budget),
        entropy=entropy_ledger,
        execution_store=execution_config.execution_store,
        run_id=run_id,
        resume_from_step_index=resume_from_step_index,
        starting_event_index=starting_event_index,
        starting_evidence_index=starting_evidence_index,
        starting_tool_invocation_index=starting_tool_invocation_index,
        starting_entropy_index=starting_entropy_index,
        initial_claim_ids=initial_claim_ids,
        initial_artifacts=initial_artifacts,
        initial_evidence=initial_evidence,
        initial_tool_invocations=initial_tool_invocations,
        _step_evidence={},
        _step_artifacts={},
        observed_run=execution_config.observed_run,
    )

    outcome = strategy.execute(resolved_flow, context)
    result = FlowRunResult(
        resolved_flow=resolved_flow,
        trace=outcome.trace,
        artifacts=outcome.artifacts,
        evidence=outcome.evidence,
        reasoning_bundles=outcome.reasoning_bundles,
        verification_results=outcome.verification_results,
        verification_arbitrations=outcome.verification_arbitrations,
        run_id=run_id,
    )
    enforce_runtime_semantics(result, mode=execution_config.mode.value)
    result = _persist_run(result, execution_config)
    return result


def _derive_seed_token(plan: ExecutionSteps) -> str | None:
    if not plan.steps:
        return None
    for step in plan.steps:
        if not step.inputs_fingerprint:
            return None
    return plan.steps[0].inputs_fingerprint


def _persist_run(result: FlowRunResult, config: ExecutionConfig) -> FlowRunResult:
    store = config.execution_store
    if store is None:
        raise ValueError("execution_store is required for persisted runs")
    plan = result.resolved_flow.plan
    run_id = result.run_id
    if run_id is None:
        store.register_dataset(plan.dataset)
        run_id = store.begin_run(plan=plan, mode=config.mode)
        store.save_steps(run_id=run_id, tenant_id=plan.tenant_id, plan=plan)
    if result.trace is not None:
        if config.mode in {RunMode.DRY_RUN, RunMode.OBSERVE}:
            store.save_events(
                run_id=run_id, tenant_id=plan.tenant_id, events=result.trace.events
            )
            store.append_tool_invocations(
                run_id=run_id,
                tenant_id=plan.tenant_id,
                tool_invocations=result.trace.tool_invocations,
                starting_index=0,
            )
            store.append_entropy_usage(
                run_id=run_id,
                usage=result.trace.entropy_usage,
                starting_index=0,
            )
            store.save_artifacts(run_id=run_id, artifacts=result.artifacts)
            store.append_evidence(
                run_id=run_id,
                evidence=result.evidence,
                starting_index=0,
            )
            store.append_claim_ids(
                run_id=run_id,
                tenant_id=plan.tenant_id,
                claim_ids=result.trace.claim_ids,
            )
        store.finalize_run(run_id=run_id, trace=result.trace)
    return FlowRunResult(
        resolved_flow=result.resolved_flow,
        trace=result.trace,
        artifacts=result.artifacts,
        evidence=result.evidence,
        reasoning_bundles=result.reasoning_bundles,
        verification_results=result.verification_results,
        verification_arbitrations=result.verification_arbitrations,
        run_id=run_id,
    )


def _resolve_read_store(config: ExecutionConfig) -> ExecutionReadStoreProtocol:
    if config.execution_read_store is not None:
        return config.execution_read_store
    if isinstance(config.execution_store, DuckDBExecutionWriteStore):
        return DuckDBExecutionReadStore(config.execution_store.path)
    raise ValueError("execution_read_store is required for resume")


def _load_resume_state(
    store: ExecutionReadStoreProtocol,
    *,
    run_id: RunID,
    tenant_id: TenantID,
) -> ResumeState:
    events = store.load_events(run_id, tenant_id=tenant_id)
    artifacts = store.load_artifacts(run_id, tenant_id=tenant_id)
    evidence = store.load_evidence(run_id, tenant_id=tenant_id)
    tool_invocations = store.load_tool_invocations(run_id, tenant_id=tenant_id)
    entropy_usage = store.load_entropy_usage(run_id, tenant_id=tenant_id)
    claim_ids = store.load_claim_ids(run_id, tenant_id=tenant_id)
    checkpoint = store.load_checkpoint(run_id, tenant_id=tenant_id)
    resume_from_step_index = -1
    starting_event_index = 0
    if events:
        starting_event_index = events[-1].event_index + 1
        resume_from_step_index = max(
            (
                event.step_index
                for event in events
                if event.event_type.value == "STEP_END"
            ),
            default=resume_from_step_index,
        )
    if checkpoint is not None:
        resume_from_step_index = checkpoint[0]
        starting_event_index = max(starting_event_index, checkpoint[1] + 1)
    return ResumeState(
        resume_from_step_index=resume_from_step_index,
        starting_event_index=starting_event_index,
        starting_evidence_index=len(evidence),
        starting_tool_invocation_index=len(tool_invocations),
        starting_entropy_index=len(entropy_usage),
        events=events,
        artifacts=artifacts,
        evidence=evidence,
        tool_invocations=tool_invocations,
        entropy_usage=entropy_usage,
        claim_ids=claim_ids,
    )


__all__ = ["ExecutionConfig", "FlowRunResult", "RunMode", "execute_flow"]
