# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayEnvelope:
    spec_version: str
    min_claim_overlap: float
    max_contradiction_delta: int
    require_same_arbitration: bool


__all__ = ["ReplayEnvelope"]
