# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_flows.runtime.observability.execution_store import DuckDBExecutionStore
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)
from agentic_flows.runtime.orchestration.replay_store import replay_with_store

pytestmark = pytest.mark.regression


def test_duckdb_replay_diff_is_clean(tmp_path: Path, resolved_flow) -> None:
    db_path = tmp_path / "history.duckdb"
    store = DuckDBExecutionStore(db_path)
    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.DRY_RUN),
    )
    store.save_trace(result.trace)
    store.save_entropy_usage(
        result.trace.flow_id, result.trace.tenant_id, result.trace.entropy_usage
    )
    store.save_replay_envelope(
        result.trace.flow_id, result.trace.tenant_id, result.trace.replay_envelope
    )

    diff, _ = replay_with_store(
        store=store,
        flow_id=result.trace.flow_id,
        tenant_id=result.trace.tenant_id,
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.DRY_RUN),
    )
    assert diff == {}
