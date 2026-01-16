import hashlib


def deterministic_seed(step_index: int, inputs_fingerprint: str) -> int:
    payload = f"{step_index}:{inputs_fingerprint}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:8], 16)
