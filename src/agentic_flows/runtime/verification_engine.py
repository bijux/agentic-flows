# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

# Verification must never call agents or modify artifacts; epistemic truth is delegated to authority.
from __future__ import annotations

from agentic_flows.core.authority import evaluate_verification
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_result import VerificationResult


class VerificationEngine:
    def verify(
        self,
        reasoning: ReasoningBundle,
        evidence: list[RetrievedEvidence],
        policy: VerificationPolicy,
    ) -> VerificationResult:
        return evaluate_verification(reasoning, policy)
