# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentic_flows.runtime.artifact_store import ArtifactStore
from agentic_flows.runtime.observability.trace_recorder import TraceRecorder
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.ontology.ids import EnvironmentFingerprint


class RunMode(str, Enum):
    PLAN = "plan"
    DRY_RUN = "dry-run"
    LIVE = "live"


@dataclass(frozen=True)
class ExecutionContext:
    seed: str | None
    environment_fingerprint: EnvironmentFingerprint
    artifact_store: ArtifactStore
    trace_recorder: TraceRecorder
    mode: RunMode
    verification_policy: VerificationPolicy | None
    step_evidence: dict[int, list[RetrievedEvidence]]
    step_artifacts: dict[int, list[Artifact]]


__all__ = ["ExecutionContext", "RunMode"]
