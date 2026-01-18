# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

REPLAY_BREAKERS = frozenset(
    {
        "plan_hash",
        "environment_fingerprint",
        "step_order",
        "artifact_content",
    }
)

DETERMINISM_BREAKERS = frozenset(
    {
        "environment_fingerprint",
        "tool_versions",
        "random_seed",
    }
)

ALLOWED_EVOLUTION = frozenset(
    {
        "doc_text",
        "non_semantic_metadata",
    }
)


def breaks_replay(change: str) -> bool:
    return change in REPLAY_BREAKERS


def breaks_determinism(change: str) -> bool:
    return change in DETERMINISM_BREAKERS


def allowed_to_evolve(change: str) -> bool:
    return change in ALLOWED_EVOLUTION


__all__ = ["allowed_to_evolve", "breaks_determinism", "breaks_replay"]
