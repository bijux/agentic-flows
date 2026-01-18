# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology import EventType


@dataclass(frozen=True)
class ExecutionEvent:
    spec_version: str
    event_index: int
    step_index: int
    event_type: EventType
    timestamp_utc: str
    payload_hash: str


__all__ = ["ExecutionEvent"]
