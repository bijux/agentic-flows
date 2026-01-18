# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentic_flows.runtime.artifact_store import ArtifactStore
from agentic_flows.runtime.trace_recorder import TraceRecorder
from agentic_flows.spec.ids import EnvironmentFingerprint
from agentic_flows.spec.verification import VerificationPolicy


class RunMode(str, Enum):
    PLAN = "plan"
    DRY_RUN = "dry-run"
    LIVE = "live"


@dataclass(frozen=True)
class RuntimeContext:
    environment_fingerprint: EnvironmentFingerprint
    artifact_store: ArtifactStore
    trace_recorder: TraceRecorder
    run_mode: RunMode
    verification_policy: VerificationPolicy | None


__all__ = ["RunMode", "RuntimeContext"]
