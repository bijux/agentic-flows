# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from agentic_flows.core.errors import SemanticViolationError
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.verification import VerificationPolicy
from agentic_flows.spec.model.verification_result import VerificationResult
from agentic_flows.spec.ontology.ids import RuleID
from agentic_flows.spec.ontology.ontology import EventType, VerificationPhase

SEMANTICS_VERSION = "v1"
SEMANTICS_SOURCE = "docs/guarantees/system_guarantees.md"

SEMANTIC_DOMAIN = "structural_truth"
VERIFICATION_DOMAIN = "epistemic_truth"

Mode = Literal["plan", "dry-run", "live"]


class _Event(Protocol):
    event_type: EventType


class _Trace(Protocol):
    finalized: bool
    events: Sequence[_Event]


class _RunResult(Protocol):
    trace: _Trace | None
    verification_results: Sequence[object]
    reasoning_bundles: Sequence[object]


@dataclass(frozen=True)
class AuthorityToken:
    scope: str = "agentic_flows.authority"


def authority_token() -> AuthorityToken:
    return AuthorityToken()


def enforce_runtime_semantics(result: _RunResult, *, mode: Mode) -> None:
    if mode == "plan":
        return
    _require_trace_finalized(result)
    if mode == "live":
        _require_verification_once_per_step(result)


def finalize_trace(trace) -> None:
    if object.__getattribute__(trace, "finalized"):
        raise SemanticViolationError("execution trace already finalized")
    trace.finalize()


def evaluate_verification(
    reasoning: ReasoningBundle,
    policy: VerificationPolicy,
) -> VerificationResult:
    violations = baseline_violations(reasoning)
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


def baseline_violations(reasoning: ReasoningBundle) -> tuple[RuleID, ...]:
    violations: list[RuleID] = []

    if any(len(claim.supported_by) == 0 for claim in reasoning.claims):
        violations.append(RuleID("claim_requires_evidence"))

    if any(not (0.0 <= claim.confidence <= 1.0) for claim in reasoning.claims):
        violations.append(RuleID("confidence_in_range"))

    claim_ids = [claim.claim_id for claim in reasoning.claims]
    if len(set(claim_ids)) != len(claim_ids):
        violations.append(RuleID("unique_claim_ids"))

    return tuple(violations)


def _require_trace_finalized(result: _RunResult) -> None:
    if result.trace is None:
        raise SemanticViolationError("execution trace must be returned for execution")
    if not result.trace.finalized:
        raise SemanticViolationError("execution trace must be finalized before return")


def _require_verification_once_per_step(result: _RunResult) -> None:
    if len(result.verification_results) == len(result.reasoning_bundles):
        return
    trace = result.trace
    if trace is None:
        raise SemanticViolationError("verification must run exactly once per step")
    failure_events = {
        EventType.REASONING_FAILED,
        EventType.RETRIEVAL_FAILED,
        EventType.STEP_FAILED,
    }
    if not _has_event(trace.events, failure_events):
        raise SemanticViolationError("verification must run exactly once per step")


def _has_event(events: Iterable[_Event], failure_events: set[EventType]) -> bool:
    return any(event.event_type in failure_events for event in events)


__all__ = [
    "AuthorityToken",
    "Mode",
    "SEMANTIC_DOMAIN",
    "SEMANTICS_SOURCE",
    "SEMANTICS_VERSION",
    "VERIFICATION_DOMAIN",
    "authority_token",
    "baseline_violations",
    "enforce_runtime_semantics",
    "evaluate_verification",
    "finalize_trace",
]
