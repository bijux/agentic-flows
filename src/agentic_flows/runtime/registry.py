# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.execution.agent_executor import AgentExecutor
from agentic_flows.runtime.execution.reasoning_executor import ReasoningExecutor
from agentic_flows.runtime.execution.retrieval_executor import RetrievalExecutor
from agentic_flows.runtime.execution.step_executor import StepExecutor
from agentic_flows.spec.model.resolved_step import ResolvedStep
from agentic_flows.spec.ontology.ontology import StepType


def build_step_registry() -> dict[StepType, StepExecutor[ResolvedStep, object]]:
    return {
        StepType.AGENT: AgentExecutor(),
        StepType.RETRIEVAL: RetrievalExecutor(),
        StepType.REASONING: ReasoningExecutor(),
    }


__all__ = ["build_step_registry"]
