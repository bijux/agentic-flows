# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib

from agentic_flows.runtime.context import ExecutionContext
from agentic_flows.spec.ontology.ontology import EntropyMagnitude, EntropySource


class DeterministicRng:
    def __init__(self, seed: str) -> None:
        self._seed = seed
        self._counter = 0

    def _digest(self) -> bytes:
        payload = f"{self._seed}:{self._counter}".encode()
        self._counter += 1
        return hashlib.sha256(payload).digest()

    def random(self) -> float:
        return int.from_bytes(self._digest()[:8], "big") / 2**64

    def randint(self, lower: int, upper: int) -> int:
        if upper < lower:
            raise ValueError("upper must be >= lower")
        span = upper - lower + 1
        return lower + int(self.random() * span)

    def randbytes(self, length: int) -> bytes:
        if length < 0:
            raise ValueError("length must be >= 0")
        chunks: list[bytes] = []
        remaining = length
        while remaining:
            digest = self._digest()
            take = min(remaining, len(digest))
            chunks.append(digest[:take])
            remaining -= take
        return b"".join(chunks)


def seeded_rng(
    context: ExecutionContext, *, step_index: int | None, description: str
) -> DeterministicRng:
    context.record_entropy(
        source=EntropySource.SEEDED_RNG,
        magnitude=EntropyMagnitude.LOW,
        description=description,
        step_index=step_index,
    )
    seed = context.seed or "seedless"
    return DeterministicRng(seed)


def external_oracle(
    context: ExecutionContext, *, step_index: int | None, description: str
) -> None:
    context.record_entropy(
        source=EntropySource.EXTERNAL_ORACLE,
        magnitude=EntropyMagnitude.HIGH,
        description=description,
        step_index=step_index,
    )


def human_input(
    context: ExecutionContext, *, step_index: int | None, description: str
) -> None:
    context.record_entropy(
        source=EntropySource.HUMAN_INPUT,
        magnitude=EntropyMagnitude.MEDIUM,
        description=description,
        step_index=step_index,
    )


__all__ = ["DeterministicRng", "external_oracle", "human_input", "seeded_rng"]
