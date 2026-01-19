# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentic_flows.core.authority import AuthorityToken
from agentic_flows.runtime.artifact_store import ArtifactStore
from agentic_flows.runtime.budget import BudgetState
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
    authority: AuthorityToken
    seed: str | None
    environment_fingerprint: EnvironmentFingerprint
    artifact_store: ArtifactStore
    trace_recorder: TraceRecorder
    mode: RunMode
    verification_policy: VerificationPolicy | None
    budget: BudgetState
    _step_evidence: dict[int, tuple[RetrievedEvidence, ...]]
    _step_artifacts: dict[int, tuple[Artifact, ...]]

    def record_evidence(
        self, step_index: int, evidence: list[RetrievedEvidence]
    ) -> None:
        self._step_evidence[step_index] = tuple(evidence)

    def record_artifacts(self, step_index: int, artifacts: list[Artifact]) -> None:
        for artifact in artifacts:
            self.artifact_store.load(artifact.artifact_id)
        self._step_artifacts[step_index] = tuple(artifacts)

    def evidence_for_step(self, step_index: int) -> tuple[RetrievedEvidence, ...]:
        return self._step_evidence.get(step_index, ())

    def artifacts_for_step(self, step_index: int) -> tuple[Artifact, ...]:
        return self._step_artifacts.get(step_index, ())

    def consume_budget(
        self, *, steps: int = 0, tokens: int = 0, artifacts: int = 0
    ) -> None:
        self.budget.consume(steps=steps, tokens=tokens, artifacts=artifacts)


__all__ = ["RunMode"]
