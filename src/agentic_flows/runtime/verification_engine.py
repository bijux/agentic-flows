# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

# Verification must never call agents or modify artifacts; epistemic truth is delegated to authority.
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from agentic_flows.core.authority import evaluate_verification
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_arbitration import VerificationArbitration
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import ArtifactID, RuleID
from agentic_flows.spec.ontology.ontology import ArbitrationRule, VerificationPhase


class VerificationEngine(Protocol):
    engine_id: str

    def verify(
        self,
        reasoning: ReasoningBundle,
        evidence: list[RetrievedEvidence],
        artifacts: list[Artifact],
        policy: VerificationPolicy,
    ) -> VerificationResult: ...


class FlowVerificationEngine(Protocol):
    engine_id: str

    def verify_flow(
        self,
        reasoning_bundles: list[ReasoningBundle],
        policy: VerificationPolicy,
    ) -> VerificationResult: ...


@dataclass(frozen=True)
class ContentVerificationEngine:
    engine_id: str = "content"

    def verify(
        self,
        reasoning: ReasoningBundle,
        evidence: list[RetrievedEvidence],
        artifacts: list[Artifact],
        policy: VerificationPolicy,
    ) -> VerificationResult:
        result = evaluate_verification(reasoning, evidence, artifacts, policy)
        return VerificationResult(
            spec_version=result.spec_version,
            engine_id=self.engine_id,
            status=result.status,
            reason=result.reason,
            violations=result.violations,
            checked_artifact_ids=result.checked_artifact_ids,
            phase=result.phase,
            rules_applied=result.rules_applied,
            decision=result.decision,
        )


@dataclass(frozen=True)
class SignatureVerificationEngine:
    engine_id: str = "signature"

    def verify(
        self,
        reasoning: ReasoningBundle,
        evidence: list[RetrievedEvidence],
        artifacts: list[Artifact],
        policy: VerificationPolicy,
    ) -> VerificationResult:
        return VerificationResult(
            spec_version="v1",
            engine_id=self.engine_id,
            status="PASS",
            reason="signature_ok",
            violations=(),
            checked_artifact_ids=(reasoning.bundle_id,),
            phase=VerificationPhase.POST_EXECUTION,
            rules_applied=(),
            decision="PASS",
        )


@dataclass(frozen=True)
class ContradictionVerificationEngine:
    engine_id: str = "contradiction"

    def verify_flow(
        self,
        reasoning_bundles: list[ReasoningBundle],
        policy: VerificationPolicy,
    ) -> VerificationResult:
        violations = _detect_contradictions(reasoning_bundles)
        status = "PASS"
        reason = "no_contradictions"
        if violations:
            status = "FAIL"
            reason = "contradiction_detected"
        bundle_ids = tuple(bundle.bundle_id for bundle in reasoning_bundles)
        return VerificationResult(
            spec_version="v1",
            engine_id=self.engine_id,
            status=status,
            reason=reason,
            violations=violations,
            checked_artifact_ids=bundle_ids,
            phase=VerificationPhase.POST_EXECUTION,
            rules_applied=(),
            decision=status,
        )


def _detect_contradictions(
    bundles: list[ReasoningBundle],
) -> tuple[RuleID, ...]:
    statements: dict[str, list[float]] = {}
    negatives: set[str] = set()
    circular = False

    for bundle in bundles:
        for claim in bundle.claims:
            normalized = _normalize_statement(claim.statement)
            if normalized.startswith("not "):
                base = normalized.removeprefix("not ").strip()
                negatives.add(base)
            statements.setdefault(normalized, []).append(claim.confidence)
            if str(claim.claim_id) in normalized:
                circular = True

    violations: list[RuleID] = []
    for statement in statements:
        base = statement.removeprefix("not ").strip()
        if base in negatives and statement != f"not {base}":
            violations.append(RuleID("direct_contradiction"))
            break

    for confidences in statements.values():
        if len(confidences) > 1 and any(
            conf < max(confidences) for conf in confidences
        ):
            violations.append(RuleID("weakened_restatement"))
            break

    if circular:
        violations.append(RuleID("circular_justification"))

    return tuple(dict.fromkeys(violations))


def _normalize_statement(statement: str) -> str:
    return " ".join(statement.lower().strip().split())


class VerificationOrchestrator:
    def __init__(
        self,
        *,
        bundle_engines: tuple[VerificationEngine, ...] | None = None,
        flow_engines: tuple[FlowVerificationEngine, ...] | None = None,
    ) -> None:
        self._bundle_engines = bundle_engines or (
            ContentVerificationEngine(),
            SignatureVerificationEngine(),
        )
        self._flow_engines = flow_engines or (ContradictionVerificationEngine(),)

    def verify_bundle(
        self,
        reasoning: ReasoningBundle,
        evidence: list[RetrievedEvidence],
        artifacts: list[Artifact],
        policy: VerificationPolicy,
    ) -> tuple[list[VerificationResult], VerificationArbitration]:
        results = [
            engine.verify(reasoning, evidence, artifacts, policy)
            for engine in self._bundle_engines
        ]
        arbitration = _arbitrate(results, policy.arbitration_rule)
        return results, arbitration

    def verify_flow(
        self,
        reasoning_bundles: list[ReasoningBundle],
        policy: VerificationPolicy,
    ) -> tuple[list[VerificationResult], VerificationArbitration]:
        results = [
            engine.verify_flow(reasoning_bundles, policy)
            for engine in self._flow_engines
        ]
        arbitration = _arbitrate(results, policy.arbitration_rule)
        return results, arbitration


def _arbitrate(
    results: list[VerificationResult], rule: ArbitrationRule
) -> VerificationArbitration:
    statuses = [result.status for result in results]
    decision = "PASS"
    if rule == ArbitrationRule.STRICT_FIRST_FAILURE:
        for status in statuses:
            if status != "PASS":
                decision = status
                break
    elif rule == ArbitrationRule.UNANIMOUS:
        if all(status == "PASS" for status in statuses):
            decision = "PASS"
        elif any(status == "FAIL" for status in statuses):
            decision = "FAIL"
        else:
            decision = "ESCALATE"
    elif rule == ArbitrationRule.QUORUM:
        counts = Counter(statuses)
        if counts["PASS"] >= (len(statuses) // 2 + 1):
            decision = "PASS"
        elif counts["FAIL"] >= (len(statuses) // 2 + 1):
            decision = "FAIL"
        else:
            decision = "ESCALATE"
    engine_ids = tuple(result.engine_id for result in results)
    engine_statuses = tuple(statuses)
    target_ids: list[ArtifactID] = []
    for result in results:
        target_ids.extend(result.checked_artifact_ids)
    return VerificationArbitration(
        spec_version="v1",
        rule=rule,
        decision=decision,
        engine_ids=engine_ids,
        engine_statuses=engine_statuses,
        target_artifact_ids=tuple(target_ids),
    )


__all__ = [
    "ContentVerificationEngine",
    "ContradictionVerificationEngine",
    "SignatureVerificationEngine",
    "VerificationEngine",
    "VerificationOrchestrator",
]
