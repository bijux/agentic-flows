# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology.ontology import EntropyMagnitude, EntropySource


@dataclass(frozen=True)
class EntropyBudget:
    spec_version: str
    allowed_sources: tuple[EntropySource, ...]
    max_magnitude: EntropyMagnitude


__all__ = ["EntropyBudget"]
