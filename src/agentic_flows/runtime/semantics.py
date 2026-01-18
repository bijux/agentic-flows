# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from typing import TYPE_CHECKING

from agentic_flows.errors import SemanticViolationError
from agentic_flows.runtime.context import RunMode
from agentic_flows.spec.ontology.ontology import EventType

if TYPE_CHECKING:
    from agentic_flows.runtime.orchestration.run_flow import FlowRunResult


def enforce_runtime_semantics(result: FlowRunResult, *, mode: RunMode) -> None:
    if mode == RunMode.PLAN:
        return
    _require_trace_finalized(result)
    if mode == RunMode.LIVE:
        _require_verification_once_per_step(result)


def _require_trace_finalized(result: FlowRunResult) -> None:
    if result.trace is None:
        raise SemanticViolationError("execution trace must be returned for execution")
    if not result.trace.finalized:
        raise SemanticViolationError("execution trace must be finalized before return")


def _require_verification_once_per_step(result: FlowRunResult) -> None:
    if len(result.verification_results) == len(result.reasoning_bundles):
        return
    if result.trace is None:
        raise SemanticViolationError("verification must run exactly once per step")
    failure_events = {
        EventType.REASONING_FAILED,
        EventType.RETRIEVAL_FAILED,
        EventType.STEP_FAILED,
    }
    if not any(event.event_type in failure_events for event in result.trace.events):
        raise SemanticViolationError("verification must run exactly once per step")


__all__ = ["enforce_runtime_semantics"]
