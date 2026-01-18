# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Literal, Protocol

from agentic_flows.core.errors import SemanticViolationError
from agentic_flows.spec.ontology.ontology import EventType

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


def enforce_runtime_semantics(result: _RunResult, *, mode: Mode) -> None:
    if mode == "plan":
        return
    _require_trace_finalized(result)
    if mode == "live":
        _require_verification_once_per_step(result)


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


__all__ = ["Mode", "enforce_runtime_semantics"]
