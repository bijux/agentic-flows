# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

# Verification must never call agents or modify artifacts; repeatability is expected when inputs match.
from __future__ import annotations

from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import RuleID
from agentic_flows.spec.ontology.ontology import VerificationPhase


class VerificationEngine:
    def verify(
        self,
        reasoning: ReasoningBundle,
        evidence: list[RetrievedEvidence],
        policy: VerificationPolicy,
    ) -> VerificationResult:
        violations = self._baseline_violations(reasoning)
        status = "PASS"
        reason = "verification_passed"

        if violations:
            status = "FAIL"
            reason = "baseline_rule_violation"

        if status == "PASS":
            if any(rule_id in policy.fail_on for rule_id in violations):
                status = "FAIL"
                reason = "policy_fail_on"
            elif any(rule_id in policy.escalate_on for rule_id in violations):
                status = "ESCALATE"
                reason = "policy_escalate_on"

        return VerificationResult(
            spec_version="v1",
            status=status,
            reason=reason,
            violations=tuple(violations),
            checked_artifact_ids=(reasoning.bundle_id,),
            phase=VerificationPhase.POST_EXECUTION,
            rules_applied=tuple(rule.rule_id for rule in policy.rules),
            decision=status,
        )

    @staticmethod
    def _baseline_violations(reasoning: ReasoningBundle) -> tuple[RuleID, ...]:
        violations: list[RuleID] = []

        if any(len(claim.supported_by) == 0 for claim in reasoning.claims):
            violations.append(RuleID("claim_requires_evidence"))

        if any(not (0.0 <= claim.confidence <= 1.0) for claim in reasoning.claims):
            violations.append(RuleID("confidence_in_range"))

        claim_ids = [claim.claim_id for claim in reasoning.claims]
        if len(set(claim_ids)) != len(claim_ids):
            violations.append(RuleID("unique_claim_ids"))

        return tuple(violations)
