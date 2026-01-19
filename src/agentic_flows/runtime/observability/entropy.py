# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.ontology.ids import TenantID
from agentic_flows.spec.ontology.ontology import EntropyMagnitude, EntropySource

_MAGNITUDE_ORDER = {
    EntropyMagnitude.LOW: 0,
    EntropyMagnitude.MEDIUM: 1,
    EntropyMagnitude.HIGH: 2,
}


class EntropyLedger:
    def __init__(self, budget: EntropyBudget | None) -> None:
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
    ) -> None:
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
            )
        )

    def seed(self, records: tuple[EntropyUsage, ...]) -> None:
        self._records.extend(records)

    def usage(self) -> tuple[EntropyUsage, ...]:
        return tuple(self._records)


__all__ = ["EntropyLedger"]
