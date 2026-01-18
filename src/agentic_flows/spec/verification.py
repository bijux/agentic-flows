# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ids import EvidenceID, RuleID
from agentic_flows.spec.verification_rule import VerificationRule


@dataclass
class VerificationPolicy:
    spec_version: str
    verification_level: str
    failure_mode: str
    required_evidence: tuple[EvidenceID, ...]
    rules: tuple[VerificationRule, ...]
    fail_on: tuple[RuleID, ...]
    escalate_on: tuple[RuleID, ...]


__all__ = ["VerificationPolicy"]
