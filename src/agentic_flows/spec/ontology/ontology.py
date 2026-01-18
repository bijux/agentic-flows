# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from enum import Enum, auto

from agentic_flows.spec.ontology.ids import ActionID as Action
from agentic_flows.spec.ontology.ids import AgentID as Agent
from agentic_flows.spec.ontology.ids import ArtifactID as Artifact
from agentic_flows.spec.ontology.ids import EvidenceID as Evidence
from agentic_flows.spec.ontology.ids import FlowID as Flow
from agentic_flows.spec.ontology.ids import StepID as Step
from agentic_flows.spec.ontology.ids import ToolID as Tool


class ArtifactType(str, Enum):
    FLOW_MANIFEST = "flow_manifest"
    EXECUTION_PLAN = "execution_plan"
    RESOLVED_STEP = "resolved_step"
    AGENT_INVOCATION = "agent_invocation"
    RETRIEVAL_REQUEST = "retrieval_request"
    RETRIEVED_EVIDENCE = "retrieved_evidence"
    REASONING_STEP = "reasoning_step"
    REASONING_CLAIM = "reasoning_claim"
    REASONING_BUNDLE = "reasoning_bundle"
    VERIFICATION_RULE = "verification_rule"
    VERIFICATION_RESULT = "verification_result"
    EXECUTION_EVENT = "execution_event"
    EXECUTION_TRACE = "execution_trace"


class ArtifactScope(str, Enum):
    EPHEMERAL = "ephemeral"
    WORKING = "working"
    AUDIT = "audit"


class EventType(str, Enum):
    def _generate_next_value_(name, start, count, last_values):  # noqa: N805
        return name

    STEP_START = auto()
    STEP_END = auto()
    STEP_FAILED = auto()
    RETRIEVAL_START = auto()
    RETRIEVAL_END = auto()
    RETRIEVAL_FAILED = auto()
    REASONING_START = auto()
    REASONING_END = auto()
    REASONING_FAILED = auto()
    VERIFICATION_START = auto()
    VERIFICATION_PASS = auto()
    VERIFICATION_FAIL = auto()
    VERIFICATION_ESCALATE = auto()
    TOOL_CALL_START = auto()
    TOOL_CALL_END = auto()
    TOOL_CALL_FAIL = auto()


class StepType(str, Enum):
    AGENT = "agent"
    RETRIEVAL = "retrieval"
    REASONING = "reasoning"
    VERIFICATION = "verification"


class VerificationPhase(str, Enum):
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"


__all__ = [
    "Agent",
    "Tool",
    "Action",
    "Artifact",
    "Evidence",
    "Flow",
    "Step",
    "ArtifactType",
    "ArtifactScope",
    "EventType",
    "StepType",
    "VerificationPhase",
]
