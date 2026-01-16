from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionEvent:
    event_index: int
    step_index: int
    event_type: str
    timestamp_utc: str
    payload_hash: str


__all__ = ["ExecutionEvent"]
