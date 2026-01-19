# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.observability.comparative_analysis import compare_runs
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)

pytestmark = pytest.mark.regression


def test_compare_runs_reports_overlap(resolved_flow) -> None:
    first = execute_flow(
        resolved_flow=resolved_flow, config=ExecutionConfig(mode=RunMode.DRY_RUN)
    )
    second = execute_flow(
        resolved_flow=resolved_flow, config=ExecutionConfig(mode=RunMode.DRY_RUN)
    )
    summary = compare_runs([first.trace, second.trace])
    assert summary["runs"] == 2
    assert summary["claim_overlap"] == 1.0
