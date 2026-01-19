# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology.ontology import ArbitrationRule


@dataclass(frozen=True)
class ArbitrationPolicy:
    spec_version: str
    rule: ArbitrationRule
    quorum_threshold: int | None


__all__ = ["ArbitrationPolicy"]
