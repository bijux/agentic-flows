# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterable

from agentic_flows.core.authority import AuthorityToken
from agentic_flows.spec.model.execution_event import ExecutionEvent


class AppendOnlyList(list[ExecutionEvent]):
    def __setitem__(self, *_args, **_kwargs) -> None:
        raise TypeError("execution events are append-only")

    def __delitem__(self, *_args, **_kwargs) -> None:
        raise TypeError("execution events are append-only")

    def clear(self) -> None:
        raise TypeError("execution events are append-only")

    def extend(self, _iterable: Iterable[ExecutionEvent]) -> None:
        raise TypeError("execution events are append-only")

    def insert(self, _index: int, _value: ExecutionEvent) -> None:
        raise TypeError("execution events are append-only")

    def pop(self, _index: int = -1) -> ExecutionEvent:
        raise TypeError("execution events are append-only")

    def remove(self, _value: ExecutionEvent) -> None:
        raise TypeError("execution events are append-only")

    def reverse(self) -> None:
        raise TypeError("execution events are append-only")

    def sort(self, *_args, **_kwargs) -> None:
        raise TypeError("execution events are append-only")


class TraceRecorder:
    def __init__(self) -> None:
        self._events: AppendOnlyList = AppendOnlyList()

    def record(self, event: ExecutionEvent, authority: AuthorityToken) -> None:
        if not isinstance(authority, AuthorityToken):
            raise TypeError("authority token required to record execution events")
        self._events.append(event)

    def events(self) -> tuple[ExecutionEvent, ...]:
        return tuple(self._events)
