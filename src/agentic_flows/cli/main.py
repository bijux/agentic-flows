# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from agentic_flows.api import ExecutionConfig, execute_flow
from agentic_flows.runtime.observability.execution_store import (
    DuckDBExecutionReadStore,
    DuckDBExecutionWriteStore,
)
from agentic_flows.runtime.observability.trace_diff import (
    entropy_summary,
    semantic_trace_diff,
)
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology import (
    DatasetState,
    DeterminismLevel,
    EntropyMagnitude,
    FlowState,
)
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    DatasetID,
    FlowID,
    GateID,
    RunID,
    TenantID,
)
from agentic_flows.spec.ontology.public import (
    EntropySource,
    ReplayAcceptability,
)


def _load_manifest(path: Path) -> FlowManifest:
    raw_contents = path.read_text(encoding="utf-8")
    payload = json.loads(raw_contents)
    return FlowManifest(
        spec_version="v1",
        flow_id=FlowID(payload["flow_id"]),
        tenant_id=TenantID(payload["tenant_id"]),
        flow_state=FlowState(payload["flow_state"]),
        determinism_level=DeterminismLevel(payload["determinism_level"]),
        replay_acceptability=ReplayAcceptability(payload["replay_acceptability"]),
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=tuple(
                EntropySource(source)
                for source in payload["entropy_budget"]["allowed_sources"]
            ),
            max_magnitude=EntropyMagnitude(payload["entropy_budget"]["max_magnitude"]),
        ),
        replay_envelope=ReplayEnvelope(
            spec_version="v1",
            min_claim_overlap=float(payload["replay_envelope"]["min_claim_overlap"]),
            max_contradiction_delta=int(
                payload["replay_envelope"]["max_contradiction_delta"]
            ),
        ),
        dataset=DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID(payload["dataset"]["dataset_id"]),
            tenant_id=TenantID(payload["dataset"]["tenant_id"]),
            dataset_version=payload["dataset"]["dataset_version"],
            dataset_hash=payload["dataset"]["dataset_hash"],
            dataset_state=DatasetState(payload["dataset"]["dataset_state"]),
            storage_uri=payload["dataset"]["storage_uri"],
        ),
        allow_deprecated_datasets=bool(payload["allow_deprecated_datasets"]),
        agents=tuple(AgentID(agent_id) for agent_id in payload["agents"]),
        dependencies=tuple(payload["dependencies"]),
        retrieval_contracts=tuple(
            ContractID(contract) for contract in payload["retrieval_contracts"]
        ),
        verification_gates=tuple(
            GateID(gate) for gate in payload["verification_gates"]
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentic-flows")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("manifest")
    run_parser.add_argument("--db-path", required=True)
    run_parser.add_argument("--strict-determinism", action="store_true")
    run_parser.add_argument("--json", action="store_true")

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("manifest")
    plan_parser.add_argument("--db-path")
    plan_parser.add_argument("--json", action="store_true")

    dry_run_parser = subparsers.add_parser("dry-run")
    dry_run_parser.add_argument("manifest")
    dry_run_parser.add_argument("--db-path", required=True)
    dry_run_parser.add_argument("--strict-determinism", action="store_true")
    dry_run_parser.add_argument("--json", action="store_true")

    unsafe_parser = subparsers.add_parser("unsafe-run")
    unsafe_parser.add_argument("manifest")
    unsafe_parser.add_argument("--db-path", required=True)
    unsafe_parser.add_argument("--strict-determinism", action="store_true")
    unsafe_parser.add_argument("--json", action="store_true")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_subparsers = inspect_parser.add_subparsers(dest="inspect_command")
    inspect_run_parser = inspect_subparsers.add_parser("run")
    inspect_run_parser.add_argument("run_id")
    inspect_run_parser.add_argument("--tenant-id", required=True)
    inspect_run_parser.add_argument("--db-path", required=True)
    inspect_run_parser.add_argument("--json", action="store_true")

    diff_parser = subparsers.add_parser("diff")
    diff_subparsers = diff_parser.add_subparsers(dest="diff_command")
    diff_run_parser = diff_subparsers.add_parser("run")
    diff_run_parser.add_argument("run_a")
    diff_run_parser.add_argument("run_b")
    diff_run_parser.add_argument("--tenant-id", required=True)
    diff_run_parser.add_argument("--db-path", required=True)
    diff_run_parser.add_argument("--json", action="store_true")

    explain_parser = subparsers.add_parser("explain")
    explain_subparsers = explain_parser.add_subparsers(dest="explain_command")
    explain_failure_parser = explain_subparsers.add_parser("failure")
    explain_failure_parser.add_argument("run_id")
    explain_failure_parser.add_argument("--tenant-id", required=True)
    explain_failure_parser.add_argument("--db-path", required=True)
    explain_failure_parser.add_argument("--json", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_subparsers = validate_parser.add_subparsers(dest="validate_command")
    validate_db_parser = validate_subparsers.add_parser("db")
    validate_db_parser.add_argument("--db-path", required=True)
    validate_db_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "inspect" and args.inspect_command == "run":
        _inspect_run(args, json_output=args.json)
        return
    if args.command == "diff" and args.diff_command == "run":
        _diff_runs(args, json_output=args.json)
        return
    if args.command == "explain" and args.explain_command == "failure":
        _explain_failure(args, json_output=args.json)
        return
    if args.command == "validate" and args.validate_command == "db":
        _validate_db(args, json_output=args.json)
        return

    manifest_path = Path(args.manifest)
    manifest = _load_manifest(manifest_path)

    config = ExecutionConfig.from_command(args.command)
    if getattr(args, "db_path", None):
        config = ExecutionConfig(
            mode=config.mode,
            execution_store=DuckDBExecutionWriteStore(Path(args.db_path)),
        )
    if getattr(args, "strict_determinism", False):
        config = replace(config, strict_determinism=True)
    result = execute_flow(manifest, config=config)
    _render_result(args.command, result, json_output=args.json)


def _render_result(command: str, result, *, json_output: bool) -> None:
    if json_output:
        _render_json_result(command, result)
        return
    _render_human_result(command, result)


def _render_json_result(command: str, result) -> None:
    if command == "plan":
        payload = asdict(result.resolved_flow.plan)
        print(json.dumps(payload, sort_keys=True))
        return
    if command == "dry-run":
        payload = asdict(result.trace)
        print(json.dumps(payload, sort_keys=True))
        return
    if command in {"run", "unsafe-run"}:
        payload = asdict(result.trace)
        artifact_list = [
            {"artifact_id": artifact.artifact_id, "content_hash": artifact.content_hash}
            for artifact in result.artifacts
        ]
        retrieval_requests = [
            {
                "request_id": step.retrieval_request.request_id,
                "vector_contract_id": step.retrieval_request.vector_contract_id,
            }
            for step in result.resolved_flow.plan.steps
            if step.retrieval_request is not None
        ]
        evidence_list = [
            {
                "evidence_id": item.evidence_id,
                "content_hash": item.content_hash,
                "vector_contract_id": item.vector_contract_id,
                "determinism": item.determinism,
            }
            for item in result.evidence
        ]
        claims_list = [
            {
                "claim_id": claim.claim_id,
                "confidence": claim.confidence,
                "evidence_ids": claim.supported_by,
            }
            for bundle in result.reasoning_bundles
            for claim in bundle.claims
        ]
        verification_list = [
            {
                "step_index": result.resolved_flow.plan.steps[index].step_index,
                "status": result.status,
                "rule_ids": result.violations,
                "escalated": result.status == "ESCALATE",
            }
            for index, result in enumerate(result.verification_results)
        ]
        output = {
            "trace": payload,
            "determinism_level": result.resolved_flow.plan.determinism_level,
            "replay_acceptability": result.resolved_flow.plan.replay_acceptability,
            "dataset": {
                "dataset_id": result.resolved_flow.plan.dataset.dataset_id,
                "tenant_id": result.resolved_flow.plan.dataset.tenant_id,
                "dataset_version": result.resolved_flow.plan.dataset.dataset_version,
                "dataset_hash": result.resolved_flow.plan.dataset.dataset_hash,
                "dataset_state": result.resolved_flow.plan.dataset.dataset_state,
            },
            "non_determinism_summary": entropy_summary(result.trace.entropy_usage),
            "entropy_used": [
                {
                    "source": usage.source,
                    "magnitude": usage.magnitude,
                    "description": usage.description,
                    "step_index": usage.step_index,
                }
                for usage in result.trace.entropy_usage
            ]
            if result.trace is not None
            else [],
            "replay_confidence": _replay_confidence(
                result.resolved_flow.plan.replay_acceptability
            ),
            "artifacts": artifact_list,
            "retrieval_requests": retrieval_requests,
            "retrieval_evidence": evidence_list,
            "reasoning_claims": claims_list,
            "verification": verification_list,
        }
        print(json.dumps(output, sort_keys=True))
        return
    print(json.dumps({"flow_id": result.resolved_flow.manifest.flow_id}))


def _render_human_result(command: str, result) -> None:
    if command == "plan":
        plan = result.resolved_flow.plan
        print(
            f"Plan ready: flow_id={plan.flow_id} steps={len(plan.steps)} "
            f"dataset={plan.dataset.dataset_id}"
        )
        return
    if command == "dry-run":
        trace = result.trace
        print(
            f"Dry-run trace: run_id={result.run_id} events={len(trace.events)} "
            f"artifacts={len(result.artifacts)}"
        )
        return
    if command in {"run", "unsafe-run"}:
        trace = result.trace
        entropy_count = len(trace.entropy_usage) if trace is not None else 0
        print(
            f"Run complete: run_id={result.run_id} steps={len(result.resolved_flow.plan.steps)} "
            f"artifacts={len(result.artifacts)} evidence={len(result.evidence)} "
            f"entropy_entries={entropy_count}"
        )
        return
    print(f"Flow loaded successfully: {result.resolved_flow.manifest.flow_id}")


def _normalize_for_json(value):
    if isinstance(value, tuple):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, list):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_for_json(item) for key, item in value.items()}
    if hasattr(value, "value"):
        return value.value
    return value


def _inspect_run(args: argparse.Namespace, *, json_output: bool) -> None:
    store = DuckDBExecutionReadStore(Path(args.db_path))
    trace = store.load_trace(RunID(args.run_id), tenant_id=TenantID(args.tenant_id))
    if json_output:
        payload = _normalize_for_json(asdict(trace))
        print(json.dumps(payload, sort_keys=True))
        return
    print(
        f"Run {args.run_id}: events={len(trace.events)} "
        f"tool_invocations={len(trace.tool_invocations)} "
        f"entropy_entries={len(trace.entropy_usage)}"
    )


def _diff_runs(args: argparse.Namespace, *, json_output: bool) -> None:
    store = DuckDBExecutionReadStore(Path(args.db_path))
    tenant_id = TenantID(args.tenant_id)
    trace_a = store.load_trace(RunID(args.run_a), tenant_id=tenant_id)
    trace_b = store.load_trace(RunID(args.run_b), tenant_id=tenant_id)
    diff = semantic_trace_diff(
        trace_a, trace_b, acceptability=trace_a.replay_acceptability
    )
    if json_output:
        print(json.dumps(_normalize_for_json(diff), sort_keys=True))
        return
    if diff:
        print(f"Diff detected: keys={', '.join(sorted(diff.keys()))}")
    else:
        print("Diff clean: no semantic differences")


def _explain_failure(args: argparse.Namespace, *, json_output: bool) -> None:
    store = DuckDBExecutionReadStore(Path(args.db_path))
    trace = store.load_trace(RunID(args.run_id), tenant_id=TenantID(args.tenant_id))
    failure_events = [
        event
        for event in trace.events
        if event.event_type.value
        in {
            "STEP_FAILED",
            "RETRIEVAL_FAILED",
            "REASONING_FAILED",
            "VERIFICATION_FAIL",
            "TOOL_CALL_FAIL",
            "EXECUTION_INTERRUPTED",
        }
    ]
    payload = {
        "run_id": args.run_id,
        "failure": _normalize_for_json(failure_events[-1].payload)
        if failure_events
        else None,
        "event_type": failure_events[-1].event_type.value if failure_events else None,
    }
    if json_output:
        print(json.dumps(payload, sort_keys=True))
        return
    if failure_events:
        last = failure_events[-1]
        print(
            f"Failure {last.event_type.value}: " f"{_normalize_for_json(last.payload)}"
        )
    else:
        print("No failure events recorded")


def _validate_db(args: argparse.Namespace, *, json_output: bool) -> None:
    DuckDBExecutionReadStore(Path(args.db_path))
    if json_output:
        print(json.dumps({"status": "ok"}, sort_keys=True))
        return
    print("DB validated: ok")


def _replay_confidence(acceptability: ReplayAcceptability) -> str:
    if acceptability == ReplayAcceptability.EXACT_MATCH:
        return "exact"
    if acceptability == ReplayAcceptability.INVARIANT_PRESERVING:
        return "invariant_preserving"
    if acceptability == ReplayAcceptability.STATISTICALLY_BOUNDED:
        return "statistically_bounded"
    return "unknown"
