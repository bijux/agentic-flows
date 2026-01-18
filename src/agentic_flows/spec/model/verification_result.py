# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology.ids import ArtifactID, RuleID
from agentic_flows.spec.ontology.ontology import VerificationPhase


@dataclass(frozen=True)
class VerificationResult:
    spec_version: str
    status: str
    reason: str
    violations: tuple[RuleID, ...]
    checked_artifact_ids: tuple[ArtifactID, ...]
    phase: VerificationPhase
    rules_applied: tuple[RuleID, ...]
    decision: str


__all__ = ["VerificationResult"]
