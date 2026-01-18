# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import builtins
import socket

import pytest

from agentic_flows.runtime.orchestration.planner import ExecutionPlanner
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ids import AgentID, FlowID

pytestmark = pytest.mark.unit


def test_resolve_is_pure(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = FlowManifest(
        spec_version="v1",
        flow_id=FlowID("flow-pure"),
        agents=(AgentID("agent-a"),),
        dependencies=(),
        retrieval_contracts=(),
        verification_gates=(),
    )

    original = manifest.__dict__.copy()

    def _blocked_socket(*_args, **_kwargs):
        raise AssertionError("network access is not allowed in resolve()")

    original_open = builtins.open

    def _blocked_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if args and len(args) > 1:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "+")):
            raise AssertionError("file writes are not allowed in resolve()")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(socket, "socket", _blocked_socket)
    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(
        "agentic_flows.runtime.orchestration.planner.compute_environment_fingerprint",
        lambda: "env-fingerprint",
    )

    monkeypatch.setattr(
        ExecutionPlanner, "_bijux_agent_version", "0.0.0", raising=False
    )
    monkeypatch.setattr(ExecutionPlanner, "_bijux_cli_version", "0.0.0", raising=False)
    resolved = ExecutionPlanner().resolve(manifest)

    assert manifest.__dict__ == original
    assert resolved.plan.environment_fingerprint == "env-fingerprint"
