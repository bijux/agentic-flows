# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayEnvelope:
    """Envelope equality means replay thresholds are identical; inequality implies replay acceptability changes, so diffs are rejected; the envelope exists separately from the trace to isolate contract thresholds from observed execution state."""

    spec_version: str
    min_claim_overlap: float
    max_contradiction_delta: int


__all__ = ["ReplayEnvelope"]
