# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from agentic_flows.runtime.context import ExecutionContext
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.verification_arbitration import VerificationArbitration
from agentic_flows.spec.model.verification_result import VerificationResult


@dataclass(frozen=True)
class ExecutionOutcome:
    trace: ExecutionTrace
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]
    verification_results: list[VerificationResult]
    verification_arbitrations: list[VerificationArbitration]


TStep = TypeVar("TStep", contravariant=True)
TResult = TypeVar("TResult", covariant=True)


class StepExecutor(Protocol[TStep, TResult]):
    def execute(self, step: TStep, context: ExecutionContext) -> TResult: ...


__all__ = ["ExecutionOutcome", "StepExecutor"]
