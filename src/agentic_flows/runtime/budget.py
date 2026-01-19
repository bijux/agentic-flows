# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionBudget:
    step_limit: int | None
    token_limit: int | None
    artifact_limit: int | None
    artifact_step_limit: int | None
    evidence_limit: int | None
    trace_event_limit: int | None


class BudgetState:
    def __init__(self, budget: ExecutionBudget | None) -> None:
        self._budget = budget
        self._steps = 0
        self._tokens = 0
        self._artifacts = 0
        self._trace_events = 0
        self._step_artifacts = 0

    def consume(self, *, steps: int = 0, tokens: int = 0, artifacts: int = 0) -> None:
        if self._budget is None:
            return
        self._steps += steps
        self._tokens += tokens
        self._artifacts += artifacts

        if (
            self._budget.step_limit is not None
            and self._steps > self._budget.step_limit
        ):
            raise ValueError("step budget exceeded")
        if (
            self._budget.token_limit is not None
            and self._tokens > self._budget.token_limit
        ):
            raise ValueError("token budget exceeded")
        if (
            self._budget.artifact_limit is not None
            and self._artifacts > self._budget.artifact_limit
        ):
            raise ValueError("artifact budget exceeded")

    def start_step(self) -> None:
        self._step_artifacts = 0

    def consume_step_artifacts(self, artifacts: int) -> None:
        if self._budget is None:
            return
        self._step_artifacts += artifacts
        if (
            self._budget.artifact_step_limit is not None
            and self._step_artifacts > self._budget.artifact_step_limit
        ):
            raise ValueError("artifact step budget exceeded")

    def consume_evidence(self, evidence_items: int) -> None:
        if self._budget is None:
            return
        if (
            self._budget.evidence_limit is not None
            and evidence_items > self._budget.evidence_limit
        ):
            raise ValueError("evidence budget exceeded")

    def consume_trace_events(self, events: int) -> None:
        if self._budget is None:
            return
        self._trace_events += events
        if (
            self._budget.trace_event_limit is not None
            and self._trace_events > self._budget.trace_event_limit
        ):
            raise ValueError("trace budget exceeded")


__all__ = ["BudgetState", "ExecutionBudget"]
