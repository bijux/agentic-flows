# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_flows.runtime.observability.execution_store import (
    DuckDBExecutionStore,
    MIGRATIONS_DIR,
    SCHEMA_CONTRACT_PATH,
    SCHEMA_VERSION,
)

pytestmark = pytest.mark.unit


def test_duckdb_migrations_apply(tmp_path: Path) -> None:
    db_path = tmp_path / "execution.duckdb"
    DuckDBExecutionStore(db_path)
    store = DuckDBExecutionStore(db_path)
    connection = store._connection
    rows = connection.execute(
        "SELECT version, checksum FROM schema_migrations ORDER BY version"
    ).fetchall()
    assert [int(row[0]) for row in rows] == [SCHEMA_VERSION]
    expected = DuckDBExecutionStore._hash_payload(
        (MIGRATIONS_DIR / "001_init.sql").read_text(encoding="utf-8")
    )
    assert rows[0][1] == expected
    contract_row = connection.execute(
        "SELECT schema_version, schema_hash FROM schema_contract"
    ).fetchone()
    assert contract_row is not None
    assert int(contract_row[0]) == SCHEMA_VERSION
    contract_hash = DuckDBExecutionStore._hash_payload(
        SCHEMA_CONTRACT_PATH.read_text(encoding="utf-8")
    )
    assert contract_row[1] == contract_hash


def test_duckdb_migrations_reject_future_version(tmp_path: Path) -> None:
    db_path = tmp_path / "future.duckdb"
    store = DuckDBExecutionStore(db_path)
    store._connection.execute(
        "INSERT INTO schema_migrations (version, checksum, applied_at) VALUES (?, ?, ?)",
        (SCHEMA_VERSION + 1, "deadbeef", "now"),
    )
    store._connection.commit()
    with pytest.raises(RuntimeError, match="ahead of code migrations"):
        DuckDBExecutionStore(db_path)


def test_duckdb_migrations_rollback_on_failure(tmp_path: Path, monkeypatch) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_init.sql").write_text("BROKEN SQL", encoding="utf-8")
    monkeypatch.setattr(
        "agentic_flows.runtime.observability.execution_store.MIGRATIONS_DIR",
        migrations_dir,
    )
    with pytest.raises(Exception):
        DuckDBExecutionStore(tmp_path / "broken.duckdb")


def test_schema_contract_mismatch_fails(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "contract.duckdb"
    DuckDBExecutionStore(db_path)
    contract_path = tmp_path / "schema.sql"
    contract_path.write_text("-- bad schema", encoding="utf-8")
    monkeypatch.setattr(
        "agentic_flows.runtime.observability.execution_store.SCHEMA_CONTRACT_PATH",
        contract_path,
    )
    with pytest.raises(RuntimeError, match="schema hash"):
        DuckDBExecutionStore(db_path)
