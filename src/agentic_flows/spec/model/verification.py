# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.verification_rule import VerificationRule
from agentic_flows.spec.ontology.ids import EvidenceID, RuleID


@dataclass(frozen=True)
class VerificationPolicy:
    spec_version: str
    verification_level: str
    failure_mode: str
    required_evidence: tuple[EvidenceID, ...]
    rules: tuple[VerificationRule, ...]
    fail_on: tuple[RuleID, ...]
    escalate_on: tuple[RuleID, ...]


__all__ = ["VerificationPolicy"]
