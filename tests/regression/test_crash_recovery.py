# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path

import duckdb
import pytest

from agentic_flows.runtime.observability.execution_store import (
    DuckDBExecutionReadStore,
    DuckDBExecutionWriteStore,
)
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.spec.ontology.ids import RunID, TenantID

pytestmark = pytest.mark.regression


def _run_with_crash(db_path: str, resolved_flow, verification_policy) -> None:
    os.environ["AF_CRASH_AT_STEP"] = "0"
    execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(
            mode=RunMode.LIVE,
            execution_store=DuckDBExecutionWriteStore(Path(db_path)),
            verification_policy=verification_policy,
        ),
    )


def test_crash_recovery_resume(
    tmp_path: Path,
    resolved_flow,
    baseline_policy,
) -> None:
    db_path = tmp_path / "crash.duckdb"
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=_run_with_crash,
        args=(str(db_path), resolved_flow, baseline_policy),
    )
    process.start()
    process.join()
    assert process.exitcode != 0

    connection = duckdb.connect(str(db_path))
    row = connection.execute(
        "SELECT run_id FROM runs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    run_id = RunID(row[0])

    execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(
            mode=RunMode.LIVE,
            execution_store=DuckDBExecutionWriteStore(db_path),
            verification_policy=baseline_policy,
            resume_run_id=run_id,
        ),
    )

    read_store = DuckDBExecutionReadStore(db_path)
    trace = read_store.load_trace(run_id, tenant_id=TenantID("tenant-a"))
    assert trace.finalized is True
    checkpoint = read_store.load_checkpoint(run_id, tenant_id=TenantID("tenant-a"))
    assert checkpoint is not None
    assert checkpoint[0] == 0
    assert all(
        earlier.event_index < later.event_index
        for earlier, later in zip(trace.events, trace.events[1:])
    )
