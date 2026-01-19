# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_agent
import pytest

from agentic_flows.runtime.observability.observed_run import ObservedRun
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)

pytestmark = pytest.mark.regression


def test_observer_mode_does_not_execute(resolved_flow, baseline_policy) -> None:
    bijux_agent.run = lambda **_kwargs: (_ for _ in ()).throw(
        AssertionError("observer mode must not execute agents")
    )

    recorded = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(mode=RunMode.DRY_RUN),
    )
    observed = ObservedRun(
        trace=recorded.trace,
        artifacts=recorded.artifacts,
        evidence=recorded.evidence,
        reasoning_bundles=recorded.reasoning_bundles,
    )

    result = execute_flow(
        resolved_flow=resolved_flow,
        config=ExecutionConfig(
            mode=RunMode.OBSERVE,
            verification_policy=baseline_policy,
            observed_run=observed,
        ),
    )

    assert result.trace == recorded.trace
    assert result.verification_results
