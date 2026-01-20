# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology import (
    ArbitrationRule,
    VerificationRandomness,
)
from agentic_flows.spec.ontology.ids import ArtifactID, PolicyFingerprint


@dataclass(frozen=True)
class VerificationArbitration:
    spec_version: str
    rule: ArbitrationRule
    policy_fingerprint: PolicyFingerprint
    decision: str
    randomness: VerificationRandomness
    engine_ids: tuple[str, ...]
    engine_statuses: tuple[str, ...]
    target_artifact_ids: tuple[ArtifactID, ...]


__all__ = ["VerificationArbitration"]
