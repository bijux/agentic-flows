# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Callable

from agentic_flows.core.authority import SEMANTICS_SOURCE, SEMANTICS_VERSION
from agentic_flows.runtime.orchestration.determinism_guard import validate_determinism
from agentic_flows.spec.model.execution_steps import ExecutionSteps


def enforce_flow_boundary(
    plan: ExecutionSteps,
    *,
    config_validation: Callable[[], None] | None = None,
) -> None:
    _ = (SEMANTICS_VERSION, SEMANTICS_SOURCE)
    _assert_step_order(plan)
    seed_token = _derive_seed_token(plan)
    validate_determinism(
        environment_fingerprint=plan.environment_fingerprint,
        seed=seed_token,
        unordered_normalized=True,
    )
    if config_validation is not None:
        config_validation()


def _derive_seed_token(plan: ExecutionSteps) -> str | None:
    if not plan.steps:
        return None
    for step in plan.steps:
        if not step.inputs_fingerprint:
            return None
    return plan.steps[0].inputs_fingerprint


def _assert_step_order(plan: ExecutionSteps) -> None:
    for index, step in enumerate(plan.steps):
        if step.step_index != index:
            raise ValueError("execution order must match resolver step order")
