# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
from pathlib import Path

import pytest

from agentic_flows.api import RunMode
from agentic_flows.cli import main as cli_main
from agentic_flows.runtime.orchestration.execute_flow import FlowRunResult
from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import (
    AgentID,
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class _RunCall:
    manifest: FlowManifest
    mode: RunMode


def test_cli_delegates_to_api_run_flow(tmp_path: Path, monkeypatch) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "flow_id": "flow-cli",
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
            agents=(AgentID("agent-1"),),
            dependencies=(),
            retrieval_contracts=(),
            verification_gates=(),
        ),
        plan=plan,
    )

    calls: list[_RunCall] = []

    def _fake_run_flow(manifest, *, mode=RunMode.LIVE, **_kwargs):
        calls.append(_RunCall(manifest=manifest, mode=mode))
        return FlowRunResult(
            resolved_flow=resolved,
            trace=None,
            artifacts=[],
            evidence=[],
            reasoning_bundles=[],
            verification_results=[],
        )

    cli_main_module = importlib.import_module("agentic_flows.cli.main")
    monkeypatch.setattr(cli_main_module, "execute_flow", _fake_run_flow)
    monkeypatch.setattr("sys.argv", ["agentic-flows", "plan", str(manifest_path)])

    cli_main()

    assert calls == [
        _RunCall(
            manifest=resolved.manifest,
            mode=RunMode.PLAN,
        )
    ]
