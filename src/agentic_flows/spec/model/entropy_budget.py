# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology import EntropyMagnitude
from agentic_flows.spec.ontology.public import EntropySource


@dataclass(frozen=True)
class EntropyBudget:
    """Entropy budget; misuse breaks entropy enforcement."""

    spec_version: str
    allowed_sources: tuple[EntropySource, ...]
    max_magnitude: EntropyMagnitude


__all__ = ["EntropyBudget"]
