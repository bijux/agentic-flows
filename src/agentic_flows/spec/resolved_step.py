# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.ids import AgentID, ArtifactID, InputsFingerprint
from agentic_flows.spec.ontology import StepType
from agentic_flows.spec.retrieval_request import RetrievalRequest


@dataclass(frozen=True)
class ResolvedStep:
    spec_version: str
    step_index: int
    step_type: StepType
    agent_id: AgentID
    inputs_fingerprint: InputsFingerprint
    declared_dependencies: tuple[AgentID, ...]
    expected_artifacts: tuple[ArtifactID, ...]
    agent_invocation: AgentInvocation
    retrieval_request: RetrievalRequest | None


__all__ = ["ResolvedStep"]
