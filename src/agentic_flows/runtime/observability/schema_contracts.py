# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_payload(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_schema_contract(path: Path) -> str:
    if not path.exists():
        raise RuntimeError("Schema contract file missing.")
    return path.read_text(encoding="utf-8")


def load_schema_hash(path: Path) -> str:
    if not path.exists():
        raise RuntimeError("Schema hash file missing.")
    return path.read_text(encoding="utf-8").strip()


__all__ = ["hash_payload", "load_schema_contract", "load_schema_hash"]
