# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.spec.model.resolved_flow import ResolvedFlow
from agentic_flows.spec.ontology.ontology import StepType


def validate(resolved_flow: ResolvedFlow) -> None:
    manifest_agents = set(resolved_flow.manifest.agents)
    steps = resolved_flow.plan.steps
    step_agents = [step.agent_id for step in steps]
    if len(set(step_agents)) != len(step_agents):
        raise ValueError("resolved steps must be unique per agent")
    if set(step_agents) != manifest_agents:
        raise ValueError("resolved steps must cover all agents exactly once")

    agent_to_index = {step.agent_id: step.step_index for step in steps}
    for step in steps:
        if step.step_type is not StepType.AGENT:
            raise ValueError("executor only supports StepType.AGENT steps")
        for dep in step.declared_dependencies:
            if dep not in agent_to_index:
                raise ValueError("resolved step dependency references unknown agent")
            if agent_to_index[dep] >= step.step_index:
                raise ValueError("dependencies must precede dependent steps")


__all__ = ["validate"]
