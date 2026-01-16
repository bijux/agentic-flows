from datetime import datetime, timedelta, timezone


def utc_now_deterministic(step_index: int) -> str:
    base = datetime(1970, 1, 1, tzinfo=timezone.utc)
    timestamp = base + timedelta(seconds=step_index)
    return timestamp.isoformat().replace("+00:00", "Z")
