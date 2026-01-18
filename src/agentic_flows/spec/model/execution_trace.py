# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.ontology.ids import (
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    ResolverID,
)


@dataclass(frozen=True)
class ExecutionTrace:
    spec_version: str
    flow_id: FlowID
    environment_fingerprint: EnvironmentFingerprint
    plan_hash: PlanHash
    resolver_id: ResolverID
    events: tuple[ExecutionEvent, ...]
    finalized: bool

    def finalize(self) -> ExecutionTrace:
        if object.__getattribute__(self, "finalized"):
            raise RuntimeError("ExecutionTrace already finalized")
        object.__setattr__(self, "finalized", True)
        return self

    def __getattribute__(self, name: str):
        if name in {
            "finalize",
            "__class__",
            "__dict__",
            "__getattribute__",
            "__setattr__",
        }:
            return object.__getattribute__(self, name)
        if not object.__getattribute__(self, "finalized"):
            raise RuntimeError("ExecutionTrace accessed before finalization")
        return object.__getattribute__(self, name)


__all__ = ["ExecutionTrace"]
