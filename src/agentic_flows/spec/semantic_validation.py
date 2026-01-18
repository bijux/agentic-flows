# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections import defaultdict, deque

from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ontology import StepType
from agentic_flows.spec.resolved_flow import ResolvedFlow


def validate_flow_manifest(manifest: FlowManifest) -> None:
    agents = list(manifest.agents)
    if len(set(agents)) != len(agents):
        raise ValueError("agents must be unique")
    if not agents:
        raise ValueError("flow must declare at least one agent")

    forward: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {agent: 0 for agent in agents}

    for entry in manifest.dependencies:
        parts = [part.strip() for part in entry.split(":")]
        if len(parts) != 2 or not all(parts):
            raise ValueError("dependencies must use 'agent:dependency' format")
        agent_id, dependency_id = parts
        if agent_id not in indegree or dependency_id not in indegree:
            raise ValueError("dependencies must reference known agents")
        if agent_id == dependency_id:
            raise ValueError("dependencies must not reference the same agent")
        if agent_id in forward[dependency_id]:
            continue
        forward[dependency_id].add(agent_id)
        indegree[agent_id] += 1

    queue = deque(sorted([agent for agent, degree in indegree.items() if degree == 0]))
    visited = []
    while queue:
        current = queue.popleft()
        visited.append(current)
        for dependent in sorted(forward[current]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(visited) != len(agents):
        raise ValueError("dependencies must form a reachable DAG")


def validate_resolved_flow(resolved_flow: ResolvedFlow) -> None:
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
