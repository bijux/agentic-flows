# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_agent import __version__ as bijux_agent_version
from bijux_cli import __version__ as bijux_cli_version

from agentic_flows.runtime.environment import compute_environment_fingerprint
from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import (
    AgentID,
    EnvironmentFingerprint,
    FlowID,
    InputsFingerprint,
    ResolverID,
    VersionID,
)
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.semantic_validation import validate_flow_manifest


class FlowResolver:
    resolver_id: ResolverID = ResolverID("agentic-flows:v0")
    _bijux_cli_version: str = bijux_cli_version
    _bijux_agent_version: str = bijux_agent_version

    def resolve(self, manifest: FlowManifest) -> ExecutionPlan:
        validate_flow_manifest(manifest)
        ordered_agents = self._toposort_agents(manifest)
        dependencies = self._parse_dependencies(manifest)
        steps = []
        for index, agent_id in enumerate(ordered_agents):
            declared = sorted(dependencies.get(agent_id, []))
            inputs_fingerprint = InputsFingerprint(
                fingerprint_inputs(
                    {
                        "agent_id": agent_id,
                        "declared_dependencies": declared,
                        "retrieval_contracts": list(manifest.retrieval_contracts),
                        "verification_gates": list(manifest.verification_gates),
                    }
                )
            )
            steps.append(
                ResolvedStep(
                    spec_version="v1",
                    step_index=index,
                    agent_id=AgentID(agent_id),
                    inputs_fingerprint=inputs_fingerprint,
                    declared_dependencies=tuple(AgentID(dep) for dep in declared),
                    expected_artifacts=(),
                    agent_invocation=AgentInvocation(
                        spec_version="v1",
                        agent_id=AgentID(agent_id),
                        agent_version=VersionID(self._bijux_agent_version),
                        inputs_fingerprint=inputs_fingerprint,
                        declared_outputs=(),
                        execution_mode="seeded",
                    ),
                    retrieval_request=None,
                )
            )
        return ExecutionPlan(
            spec_version="v1",
            flow_id=FlowID(manifest.flow_id),
            steps=tuple(steps),
            environment_fingerprint=EnvironmentFingerprint(
                compute_environment_fingerprint()
            ),
            resolution_metadata=(
                ("resolver_id", self.resolver_id),
                ("bijux_cli_version", self._bijux_cli_version),
            ),
        )

    def _toposort_agents(self, manifest: FlowManifest) -> list[str]:
        """Deterministic topological sort using lexical tie-breaking for stability."""
        dependencies = self._parse_dependencies(manifest)
        agents = set(manifest.agents)
        indegree = {agent: 0 for agent in agents}
        forward = {agent: [] for agent in agents}

        for agent, deps in dependencies.items():
            for dep in deps:
                forward[dep].append(agent)
                indegree[agent] += 1

        ready = sorted([agent for agent, degree in indegree.items() if degree == 0])
        ordered = []
        while ready:
            current = ready.pop(0)
            ordered.append(current)
            for downstream in sorted(forward[current]):
                indegree[downstream] -= 1
                if indegree[downstream] == 0:
                    ready.append(downstream)
                    ready.sort()

        if len(ordered) != len(agents):
            raise ValueError("dependencies contain a cycle or reference unknown agents")
        return ordered

    def _parse_dependencies(self, manifest: FlowManifest) -> dict[str, list[str]]:
        agents = set(manifest.agents)
        mapping: dict[str, list[str]] = {agent: [] for agent in agents}
        for entry in manifest.dependencies:
            parts = [part.strip() for part in entry.split(":")]
            if len(parts) != 2 or not all(parts):
                raise ValueError("dependencies must use 'agent:dependency' format")
            agent_id, dependency_id = parts
            if agent_id not in agents or dependency_id not in agents:
                raise ValueError("dependencies must reference known agents")
            mapping[agent_id].append(dependency_id)
        return mapping
