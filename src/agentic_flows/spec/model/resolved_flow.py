# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.model.execution_plan import ExecutionPlan
from agentic_flows.spec.model.flow_manifest import FlowManifest


@dataclass(frozen=True)
class ResolvedFlow:
    spec_version: str
    manifest: FlowManifest
    plan: ExecutionPlan


__all__ = ["ResolvedFlow"]
