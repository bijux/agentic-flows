# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from typing import Any

from agentic_flows.runtime.environment import compute_environment_fingerprint


def validate_determinism(
    environment_fingerprint: str | None,
    seed: Any | None,
    unordered_normalized: bool,
) -> None:
    current_fingerprint = compute_environment_fingerprint()
    if not environment_fingerprint:
        raise ValueError("environment_fingerprint is required for deterministic runs")
    if environment_fingerprint != current_fingerprint:
        raise ValueError("environment_fingerprint mismatch")
    if seed is None:
        raise ValueError("deterministic seed is required for deterministic runs")
    if not unordered_normalized:
        raise ValueError("unordered collections must be normalized before execution")
