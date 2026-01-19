# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.non_determinism_source import NonDeterminismSource
from agentic_flows.spec.ontology.ids import TenantID
from agentic_flows.spec.ontology.ontology import EntropyMagnitude, EntropySource


@dataclass(frozen=True)
class EntropyUsage:
    spec_version: str
    tenant_id: TenantID
    source: EntropySource
    magnitude: EntropyMagnitude
    description: str
    step_index: int | None
    nondeterminism_source: NonDeterminismSource


__all__ = ["EntropyUsage"]
