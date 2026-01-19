# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
from pathlib import Path

import pytest

from agentic_flows.api import ExecutionConfig, RunMode
from agentic_flows.cli import main as cli_main
from agentic_flows.runtime.orchestration.execute_flow import FlowRunResult
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.ontology.ids import (
    AgentID,
    DatasetID,
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
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

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class _RunCall:
    manifest: FlowManifest
    config: ExecutionConfig


def test_cli_delegates_to_api_run_flow(tmp_path: Path, monkeypatch) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "flow_id": "flow-cli",
                "tenant_id": "tenant-a",
                "flow_state": "validated",
                "determinism_level": "strict",
                "replay_acceptability": "exact_match",
                "entropy_budget": {
                    "allowed_sources": ["seeded_rng", "data"],
                    "max_magnitude": "low",
                },
                "dataset": {
                    "dataset_id": "dataset-cli",
                    "tenant_id": "tenant-a",
                    "dataset_version": "1.0.0",
                    "dataset_hash": "hash-cli",
                    "dataset_state": "frozen",
                    "storage_uri": "file://datasets/retrieval_corpus.jsonl",
                },
                "allow_deprecated_datasets": False,
                "replay_envelope": {
                    "min_claim_overlap": 1.0,
                    "max_contradiction_delta": 0,
                },
                "agents": ["agent-1"],
                "dependencies": [],
                "retrieval_contracts": [],
                "verification_gates": [],
            }
        ),
        encoding="utf-8",
    )

    plan = ExecutionSteps(
        spec_version="v1",
        flow_id=FlowID("flow-cli"),
        tenant_id=TenantID("tenant-a"),
        flow_state=FlowState.VALIDATED,
        determinism_level=DeterminismLevel.STRICT,
        replay_acceptability=ReplayAcceptability.EXACT_MATCH,
        entropy_budget=EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.SEEDED_RNG, EntropySource.DATA),
            max_magnitude=EntropyMagnitude.LOW,
        ),
        replay_envelope=ReplayEnvelope(
            spec_version="v1",
            min_claim_overlap=1.0,
            max_contradiction_delta=0,
        ),
        dataset=DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID("dataset-cli"),
            tenant_id=TenantID("tenant-a"),
            dataset_version="1.0.0",
            dataset_hash="hash-cli",
            dataset_state=DatasetState.FROZEN,
            storage_uri="file://datasets/retrieval_corpus.jsonl",
        ),
        allow_deprecated_datasets=False,
        steps=(),
        environment_fingerprint=EnvironmentFingerprint("env"),
        plan_hash=PlanHash("plan"),
        resolution_metadata=(("resolver_id", ResolverID("agentic-flows:v0")),),
    )
    resolved = ExecutionPlan(
        spec_version="v1",
        manifest=FlowManifest(
            spec_version="v1",
            flow_id=FlowID("flow-cli"),
            tenant_id=TenantID("tenant-a"),
            flow_state=FlowState.VALIDATED,
            determinism_level=DeterminismLevel.STRICT,
            replay_acceptability=ReplayAcceptability.EXACT_MATCH,
            entropy_budget=EntropyBudget(
                spec_version="v1",
                allowed_sources=(EntropySource.SEEDED_RNG, EntropySource.DATA),
                max_magnitude=EntropyMagnitude.LOW,
            ),
            replay_envelope=ReplayEnvelope(
                spec_version="v1",
                min_claim_overlap=1.0,
                max_contradiction_delta=0,
            ),
            dataset=DatasetDescriptor(
                spec_version="v1",
                dataset_id=DatasetID("dataset-cli"),
                tenant_id=TenantID("tenant-a"),
                dataset_version="1.0.0",
                dataset_hash="hash-cli",
                dataset_state=DatasetState.FROZEN,
                storage_uri="file://datasets/retrieval_corpus.jsonl",
            ),
            allow_deprecated_datasets=False,
            agents=(AgentID("agent-1"),),
            dependencies=(),
            retrieval_contracts=(),
            verification_gates=(),
        ),
        plan=plan,
    )

    calls: list[_RunCall] = []

    def _fake_run_flow(manifest, *, config: ExecutionConfig, **_kwargs):
        calls.append(_RunCall(manifest=manifest, config=config))
        return FlowRunResult(
            resolved_flow=resolved,
            trace=None,
            artifacts=[],
            evidence=[],
            reasoning_bundles=[],
            verification_results=[],
            verification_arbitrations=[],
            run_id=None,
        )

    cli_main_module = importlib.import_module("agentic_flows.cli.main")
    monkeypatch.setattr(cli_main_module, "execute_flow", _fake_run_flow)
    monkeypatch.setattr("sys.argv", ["agentic-flows", "plan", str(manifest_path)])

    cli_main()

    assert calls == [
        _RunCall(
            manifest=resolved.manifest,
            config=ExecutionConfig(mode=RunMode.PLAN),
        )
    ]


@pytest.mark.parametrize("missing_key", ["min_claim_overlap", "max_contradiction_delta"])
def test_cli_replay_envelope_requires_fields(
    tmp_path: Path, missing_key: str
) -> None:
    manifest_path = tmp_path / "manifest.json"
    payload = {
        "flow_id": "flow-cli",
        "tenant_id": "tenant-a",
        "flow_state": "validated",
        "determinism_level": "strict",
        "replay_acceptability": "exact_match",
        "entropy_budget": {
            "allowed_sources": ["seeded_rng", "data"],
            "max_magnitude": "low",
        },
        "dataset": {
            "dataset_id": "dataset-cli",
            "tenant_id": "tenant-a",
            "dataset_version": "1.0.0",
            "dataset_hash": "hash-cli",
            "dataset_state": "frozen",
            "storage_uri": "file://datasets/retrieval_corpus.jsonl",
        },
        "allow_deprecated_datasets": False,
        "replay_envelope": {
            "min_claim_overlap": 1.0,
            "max_contradiction_delta": 0,
        },
        "agents": ["agent-1"],
        "dependencies": [],
        "retrieval_contracts": [],
        "verification_gates": [],
    }
    payload["replay_envelope"].pop(missing_key)
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    cli_main_module = importlib.import_module("agentic_flows.cli.main")
    with pytest.raises(KeyError):
        cli_main_module._load_manifest(manifest_path)
