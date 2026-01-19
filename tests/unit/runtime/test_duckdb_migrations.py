# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from agentic_flows.runtime.observability.execution_store import (
    DuckDBExecutionStore,
    SCHEMA_VERSION,
)

pytestmark = pytest.mark.unit


def test_duckdb_migrations_apply(tmp_path: Path) -> None:
    db_path = tmp_path / "execution.duckdb"
    DuckDBExecutionStore(db_path)
    connection = duckdb.connect(str(db_path))
    row = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    assert int(row[0]) == SCHEMA_VERSION
