# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from enum import Enum

from agentic_flows.spec.ids import ActionID as Action
from agentic_flows.spec.ids import AgentID as Agent
from agentic_flows.spec.ids import ArtifactID as Artifact
from agentic_flows.spec.ids import EvidenceID as Evidence
from agentic_flows.spec.ids import FlowID as Flow
from agentic_flows.spec.ids import StepID as Step
from agentic_flows.spec.ids import ToolID as Tool


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


class EventType(str, Enum):
    STEP_START = "STEP_START"  # noqa: S105
    STEP_END = "STEP_END"  # noqa: S105
    STEP_FAILED = "STEP_FAILED"  # noqa: S105
    RETRIEVAL_START = "RETRIEVAL_START"  # noqa: S105
    RETRIEVAL_END = "RETRIEVAL_END"  # noqa: S105
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"  # noqa: S105
    REASONING_START = "REASONING_START"  # noqa: S105
    REASONING_END = "REASONING_END"  # noqa: S105
    REASONING_FAILED = "REASONING_FAILED"  # noqa: S105
    VERIFICATION_START = "VERIFICATION_START"  # noqa: S105
    VERIFICATION_PASS = "VERIFICATION_PASS"  # noqa: S105
    VERIFICATION_FAIL = "VERIFICATION_FAIL"  # noqa: S105
    VERIFICATION_ESCALATE = "VERIFICATION_ESCALATE"  # noqa: S105
    TOOL_CALL_START = "TOOL_CALL_START"  # noqa: S105
    TOOL_CALL_END = "TOOL_CALL_END"  # noqa: S105
    TOOL_CALL_FAIL = "TOOL_CALL_FAIL"  # noqa: S105


class StepType(str, Enum):
    AGENT = "agent"
    RETRIEVAL = "retrieval"
    REASONING = "reasoning"
    VERIFICATION = "verification"


__all__ = [
    "Agent",
    "Tool",
    "Action",
    "Artifact",
    "Evidence",
    "Flow",
    "Step",
    "ArtifactType",
    "EventType",
    "StepType",
]
