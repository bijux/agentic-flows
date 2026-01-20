# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence


@dataclass(frozen=True)
class ObservedRun:
    """Observed run snapshot; misuse breaks observer invariants."""

    trace: ExecutionTrace
    artifacts: list[Artifact]
    evidence: list[RetrievedEvidence]
    reasoning_bundles: list[ReasoningBundle]


__all__ = ["ObservedRun"]
