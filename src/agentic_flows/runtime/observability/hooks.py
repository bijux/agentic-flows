# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from typing import Protocol

from agentic_flows.spec.model.execution_event import ExecutionEvent


class RuntimeObserver(Protocol):
    """Runtime observer contract; misuse breaks observation guarantees."""

    def on_event(self, event: ExecutionEvent) -> None: ...


__all__ = ["RuntimeObserver"]
