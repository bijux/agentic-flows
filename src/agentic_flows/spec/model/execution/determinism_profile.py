# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for spec/model/execution/determinism_profile.py."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology import EntropyMagnitude
from agentic_flows.spec.ontology.public import EntropySource, ReplayAcceptability


@dataclass(frozen=True)
class DeterminismProfile:
    """Structured determinism profile; misuse breaks auditability."""

    spec_version: str
    entropy_magnitude: EntropyMagnitude | None
    entropy_sources: tuple[EntropySource, ...]
    replay_acceptability: ReplayAcceptability
    confidence_decay: float


__all__ = ["DeterminismProfile"]
