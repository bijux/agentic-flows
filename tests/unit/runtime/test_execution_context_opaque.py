# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import dataclasses

import pytest

from agentic_flows.core.authority import authority_token
from agentic_flows.runtime.artifact_store import InMemoryArtifactStore
from agentic_flows.runtime.context import ExecutionContext, RunMode
from agentic_flows.runtime.observability.trace_recorder import TraceRecorder
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.ontology.ids import EnvironmentFingerprint

pytestmark = pytest.mark.unit


def test_execution_context_is_opaque_and_frozen() -> None:
    context = ExecutionContext(
        authority=authority_token(),
        seed="seed",
        environment_fingerprint=EnvironmentFingerprint("env"),
        artifact_store=InMemoryArtifactStore(),
        trace_recorder=TraceRecorder(),
        mode=RunMode.DRY_RUN,
        verification_policy=VerificationPolicy(
            spec_version="v1",
            verification_level="baseline",
            failure_mode="halt",
            required_evidence=(),
            rules=(),
            fail_on=(),
            escalate_on=(),
        ),
        _step_evidence={},
        _step_artifacts={},
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        context.mode = RunMode.LIVE

    evidence = context.evidence_for_step(0)
    with pytest.raises(AttributeError):
        evidence.append("not-allowed")
