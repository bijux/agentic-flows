# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import builtins
import socket

import pytest

from agentic_flows.runtime import resolver as resolver_module
from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import AgentID, FlowID


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
    monkeypatch.setattr(resolver_module, "compute_environment_fingerprint", lambda: "env-fingerprint")

    resolver = FlowResolver()
    resolver._bijux_agent_version = "0.0.0"
    with pytest.raises(NotImplementedError):
        resolver.resolve(manifest)

    assert manifest.__dict__ == original
