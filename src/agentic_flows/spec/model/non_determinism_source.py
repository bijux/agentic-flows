# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology.ids import FlowID, StepID
from agentic_flows.spec.ontology.public import EntropySource


@dataclass(frozen=True)
class NonDeterminismSource:
    source: EntropySource
    authorized: bool
    scope: StepID | FlowID


__all__ = ["NonDeterminismSource"]
