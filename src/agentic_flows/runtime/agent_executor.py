# Agent execution is the only place bijux-agent may be invoked.
# Allowed: deterministic agent execution with explicit inputs and seeded randomness.
# Forbidden: I/O, network access, retrieval, vector search, reasoning, or memory writes.
import hashlib
from typing import Any, List, Optional

import bijux_agent

from agentic_flows.runtime.seed import deterministic_seed
from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence


class AgentExecutor:
    def execute_step(
        self, step: ResolvedStep, evidence: Optional[List[RetrievedEvidence]] = None
    ) -> List[Artifact]:
        seed = deterministic_seed(step.step_index, step.inputs_fingerprint)
        if not hasattr(bijux_agent, "run"):
            raise RuntimeError("bijux_agent.run is required for agent execution")

        outputs = bijux_agent.run(
            agent_id=step.agent_invocation.agent_id,
            seed=seed,
            inputs_fingerprint=step.inputs_fingerprint,
            declared_outputs=step.agent_invocation.declared_outputs,
            evidence=evidence or [],
        )
        return self._artifacts_from_outputs(step, outputs)

    def _artifacts_from_outputs(self, step: ResolvedStep, outputs: Any) -> List[Artifact]:
        if not isinstance(outputs, list):
            raise ValueError("agent outputs must be a list")

        artifacts = []
        for entry in outputs:
            if not isinstance(entry, dict):
                raise ValueError("agent outputs must be dict entries")
            if "artifact_id" not in entry or "artifact_type" not in entry or "content" not in entry:
                raise ValueError("agent output missing required fields")

            content_hash = self._hash_content(entry["content"])
            parent_artifacts = entry.get("parent_artifacts", [])
            if not isinstance(parent_artifacts, list):
                raise ValueError("parent_artifacts must be a list")

            artifacts.append(
                Artifact(
                    artifact_id=str(entry["artifact_id"]),
                    artifact_type=str(entry["artifact_type"]),
                    producer="agent",
                    parent_artifacts=tuple(parent_artifacts),
                    content_hash=content_hash,
                )
            )
        return artifacts

    @staticmethod
    def _hash_content(content: Any) -> str:
        payload = str(content).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
