# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable

from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology.ontology import (
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    ReplayAcceptability,
)


def validate(manifest: FlowManifest) -> None:
    _require_tuple_of_str("agents", manifest.agents)
    _require_tuple_of_str("dependencies", manifest.dependencies)
    _require_tuple_of_str("retrieval_contracts", manifest.retrieval_contracts)
    _require_tuple_of_str("verification_gates", manifest.verification_gates)
    _require_enum("determinism_level", manifest.determinism_level, DeterminismLevel)
    _require_enum(
        "replay_acceptability", manifest.replay_acceptability, ReplayAcceptability
    )
    if manifest.entropy_budget is None:
        raise ValueError("entropy_budget must be declared")
    if not isinstance(manifest.entropy_budget.allowed_sources, tuple):
        raise ValueError("entropy_budget.allowed_sources must be a tuple")
    if not manifest.entropy_budget.allowed_sources:
        raise ValueError("entropy_budget.allowed_sources must not be empty")
    for source in manifest.entropy_budget.allowed_sources:
        _require_enum("entropy_budget.allowed_sources", source, EntropySource)
    _require_enum(
        "entropy_budget.max_magnitude",
        manifest.entropy_budget.max_magnitude,
        EntropyMagnitude,
    )

    if not isinstance(manifest.flow_id, str) or not manifest.flow_id.strip():
        raise ValueError("flow_id must be a non-empty string")

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


def _require_tuple_of_str(field: str, value: Iterable[str]) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field} must be a tuple of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} must contain non-empty strings")


def _require_enum(field: str, value: object, enum_type: type) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"{field} must be a valid {enum_type.__name__}")


__all__ = ["validate"]
