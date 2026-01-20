# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for runtime/observability/classification/entropy.py."""

from __future__ import annotations

from agentic_flows.spec.model.artifact.entropy_budget import EntropyBudget
from agentic_flows.spec.model.artifact.entropy_usage import EntropyUsage
from agentic_flows.spec.model.artifact.non_determinism_source import (
    NonDeterminismSource,
)
from agentic_flows.spec.ontology import EntropyMagnitude
from agentic_flows.spec.ontology.ids import TenantID
from agentic_flows.spec.ontology.public import EntropySource

_MAGNITUDE_ORDER = {
    EntropyMagnitude.LOW: 0,
    EntropyMagnitude.MEDIUM: 1,
    EntropyMagnitude.HIGH: 2,
}


class EntropyLedger:
    """Entropy ledger; misuse breaks entropy accounting."""

    def __init__(self, budget: EntropyBudget | None) -> None:
        """Internal helper; not part of the public API."""
        self._budget = budget
        self._records: list[EntropyUsage] = []

    def record(
        self,
        *,
        tenant_id: TenantID,
        source: EntropySource,
        magnitude: EntropyMagnitude,
        description: str,
        step_index: int | None,
        nondeterminism_source: NonDeterminismSource,
    ) -> None:
        """Execute record and enforce its contract."""
        if self._budget is None:
            raise ValueError("entropy budget must be declared before entropy is used")
        if source not in self._budget.allowed_sources:
            raise ValueError("entropy source not allowed by policy")
        if _MAGNITUDE_ORDER[magnitude] > _MAGNITUDE_ORDER[self._budget.max_magnitude]:
            raise ValueError("entropy magnitude exceeds declared budget")
        self._records.append(
            EntropyUsage(
                spec_version="v1",
                tenant_id=tenant_id,
                source=source,
                magnitude=magnitude,
                description=description,
                step_index=step_index,
                nondeterminism_source=nondeterminism_source,
            )
        )

    def seed(self, records: tuple[EntropyUsage, ...]) -> None:
        """Execute seed and enforce its contract."""
        self._records.extend(records)

    def usage(self) -> tuple[EntropyUsage, ...]:
        """Execute usage and enforce its contract."""
        return tuple(self._records)


__all__ = ["EntropyLedger"]
