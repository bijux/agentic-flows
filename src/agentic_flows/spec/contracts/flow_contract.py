# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for spec/contracts/flow_contract.py."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable

from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.ontology import (
    DatasetState,
    DeterminismLevel,
    EntropyMagnitude,
    FlowState,
)
from agentic_flows.spec.ontology.public import (
    EntropySource,
    ReplayAcceptability,
)


def validate(manifest: FlowManifest) -> None:
    """Validate flow manifest; misuse breaks flow validity."""
    _require_enum("flow_state", manifest.flow_state, FlowState)
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
    if not 0.0 <= manifest.replay_envelope.min_claim_overlap <= 1.0:
        raise ValueError("replay_envelope.min_claim_overlap must be between 0 and 1")
    if manifest.replay_envelope.max_contradiction_delta < 0:
        raise ValueError("replay_envelope.max_contradiction_delta must be >= 0")
    if not manifest.dataset.dataset_id:
        raise ValueError("dataset.dataset_id must be declared")
    if not manifest.dataset.tenant_id:
        raise ValueError("dataset.tenant_id must be declared")
    if not manifest.dataset.dataset_version:
        raise ValueError("dataset.dataset_version must be declared")
    if not manifest.dataset.dataset_hash:
        raise ValueError("dataset.dataset_hash must be declared")
    _require_enum("dataset.dataset_state", manifest.dataset.dataset_state, DatasetState)
    if (
        manifest.dataset.dataset_state is DatasetState.DEPRECATED
        and not manifest.allow_deprecated_datasets
    ):
        raise ValueError("deprecated datasets require allow_deprecated_datasets")

    if not isinstance(manifest.flow_id, str) or not manifest.flow_id.strip():
        raise ValueError("flow_id must be a non-empty string")
    if not isinstance(manifest.tenant_id, str) or not manifest.tenant_id.strip():
        raise ValueError("tenant_id must be a non-empty string")

    if manifest.flow_state in {FlowState.DRAFT, FlowState.DEPRECATED}:
        raise ValueError("flow_state must allow execution")

    agents = list(manifest.agents)
    if len(set(agents)) != len(agents):
        raise ValueError("agents must be unique")
    if not agents:
        raise ValueError("flow must declare at least one agent")

    forward: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = dict.fromkeys(agents, 0)

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
    """Internal helper; not part of the public API."""
    if not isinstance(value, tuple):
        raise ValueError(f"{field} must be a tuple of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} must contain non-empty strings")


def _require_enum(field: str, value: object, enum_type: type) -> None:
    """Internal helper; not part of the public API."""
    if not isinstance(value, enum_type):
        raise ValueError(f"{field} must be a valid {enum_type.__name__}")


__all__ = ["validate"]
