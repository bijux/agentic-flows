import argparse
import json
from dataclasses import asdict
from pathlib import Path

from agentic_flows.runtime.dry_run_executor import DryRunExecutor
from agentic_flows.runtime.live_executor import LiveExecutor
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest


def _load_manifest(path: Path) -> FlowManifest:
    raw_contents = path.read_text(encoding="utf-8")
    payload = json.loads(raw_contents)
    return FlowManifest(
        flow_id=payload["flow_id"],
        agents=tuple(payload["agents"]),
        dependencies=tuple(payload["dependencies"]),
        retrieval_contracts=tuple(payload["retrieval_contracts"]),
        verification_gates=tuple(payload["verification_gates"]),
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

    if args.command == "plan":
        resolver = FlowResolver()
        plan = resolver.resolve(manifest)
        payload = asdict(plan)
        print(json.dumps(payload, sort_keys=True))
        return

    if args.command == "dry-run":
        resolver = FlowResolver()
        executor = DryRunExecutor()
        plan = resolver.resolve(manifest)
        trace = executor.execute(plan)
        payload = asdict(trace)
        print(json.dumps(payload, sort_keys=True))
        return

    if args.command == "run":
        resolver = FlowResolver()
        executor = LiveExecutor()
        plan = resolver.resolve(manifest)
        trace, artifacts, evidence, reasoning_bundles, verification_results = executor.execute(plan)
        payload = asdict(trace)
        artifact_list = [
            {"artifact_id": artifact.artifact_id, "content_hash": artifact.content_hash}
            for artifact in artifacts
        ]
        retrieval_requests = [
            {
                "request_id": step.retrieval_request.request_id,
                "vector_contract_id": step.retrieval_request.vector_contract_id,
            }
            for step in plan.steps
            if step.retrieval_request is not None
        ]
        evidence_list = [
            {
                "evidence_id": item.evidence_id,
                "content_hash": item.content_hash,
                "vector_contract_id": item.vector_contract_id,
            }
            for item in evidence
        ]
        claims_list = [
            {
                "claim_id": claim.claim_id,
                "confidence": claim.confidence,
                "evidence_ids": claim.supported_by,
            }
            for bundle in reasoning_bundles
            for claim in bundle.claims
        ]
        verification_list = [
            {
                "step_index": plan.steps[index].step_index,
                "status": result.status,
                "rule_ids": result.violations,
                "escalated": result.status == "ESCALATE",
            }
            for index, result in enumerate(verification_results)
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

    print(f"Flow loaded successfully: {manifest.flow_id}")
