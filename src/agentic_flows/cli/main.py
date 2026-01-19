# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from agentic_flows.api import ExecutionConfig, execute_flow
from agentic_flows.runtime.observability.trace_diff import entropy_summary
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology.ids import (
    AgentID,
    ContractID,
    DatasetID,
    FlowID,
    GateID,
    TenantID,
)
from agentic_flows.spec.ontology.ontology import (
    DatasetState,
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    FlowState,
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
            require_same_arbitration=bool(
                payload["replay_envelope"]["require_same_arbitration"]
            ),
        ),
        dataset=DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID(payload["dataset"]["dataset_id"]),
            tenant_id=TenantID(payload["dataset"]["tenant_id"]),
            dataset_version=payload["dataset"]["dataset_version"],
            dataset_hash=payload["dataset"]["dataset_hash"],
            dataset_state=DatasetState(payload["dataset"]["dataset_state"]),
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

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("manifest")

    dry_run_parser = subparsers.add_parser("dry-run")
    dry_run_parser.add_argument("manifest")

    unsafe_parser = subparsers.add_parser("unsafe-run")
    unsafe_parser.add_argument("manifest")

    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    manifest = _load_manifest(manifest_path)

    config = ExecutionConfig.from_command(args.command)
    result = execute_flow(manifest, config=config)
    _render_result(args.command, result)


def _render_result(command: str, result) -> None:
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
    print(f"Flow loaded successfully: {result.resolved_flow.manifest.flow_id}")


def _replay_confidence(acceptability: ReplayAcceptability) -> str:
    if acceptability == ReplayAcceptability.EXACT_MATCH:
        return "exact"
    if acceptability == ReplayAcceptability.INVARIANT_PRESERVING:
        return "invariant_preserving"
    if acceptability == ReplayAcceptability.STATISTICALLY_BOUNDED:
        return "statistically_bounded"
    return "unknown"
