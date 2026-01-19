# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib

from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.ontology.ids import ContentHash


class ExecutionStateTracker:
    def __init__(self, seed: str | None) -> None:
        self._seed = seed or "seedless"
        self._state = ContentHash(self._hash_payload(self._seed))

    def advance(self, step: ResolvedStep) -> ContentHash:
        payload = f"{self._state}:{step.agent_id}:{step.inputs_fingerprint}"
        self._state = ContentHash(self._hash_payload(payload))
        return self._state

    @staticmethod
    def _hash_payload(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["ExecutionStateTracker"]
