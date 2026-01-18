# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from agentic_flows.api import ExecutionConfig, execute_flow
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import AgentID, ContractID, FlowID, GateID


def _load_manifest(path: Path) -> FlowManifest:
    raw_contents = path.read_text(encoding="utf-8")
    payload = json.loads(raw_contents)
    return FlowManifest(
        spec_version="v1",
        flow_id=FlowID(payload["flow_id"]),
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
    if command == "run":
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
            "artifacts": artifact_list,
            "retrieval_requests": retrieval_requests,
            "retrieval_evidence": evidence_list,
            "reasoning_claims": claims_list,
            "verification": verification_list,
        }
        print(json.dumps(output, sort_keys=True))
        return
    print(f"Flow loaded successfully: {result.resolved_flow.manifest.flow_id}")
