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
    EXECUTOR_STATE = "executor_state"


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
    VERIFICATION_ARBITRATION = auto()
    EXECUTION_INTERRUPTED = auto()
    HUMAN_INTERVENTION = auto()
    SEMANTIC_VIOLATION = auto()
    TOOL_CALL_START = auto()
    TOOL_CALL_END = auto()
    TOOL_CALL_FAIL = auto()


class CausalityTag(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    DATASET = "dataset"
    ENVIRONMENT = "environment"
    HUMAN = "human"


class StepType(str, Enum):
    AGENT = "agent"
    RETRIEVAL = "retrieval"
    REASONING = "reasoning"
    VERIFICATION = "verification"


class VerificationPhase(str, Enum):
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"


class ArbitrationRule(str, Enum):
    UNANIMOUS = "unanimous"
    QUORUM = "quorum"
    STRICT_FIRST_FAILURE = "strict_first_failure"


class DeterminismLevel(str, Enum):
    STRICT = "strict"
    BOUNDED = "bounded"
    PROBABILISTIC = "probabilistic"
    UNCONSTRAINED = "unconstrained"


class DeterminismClass(str, Enum):
    STRUCTURAL = "structural"
    ENVIRONMENTAL = "environmental"
    STOCHASTIC = "stochastic"
    HUMAN = "human"
    EXTERNAL = "external"


class FlowState(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    FROZEN = "frozen"
    DEPRECATED = "deprecated"


class DatasetState(str, Enum):
    EXPERIMENTAL = "experimental"
    FROZEN = "frozen"
    DEPRECATED = "deprecated"


class ReplayAcceptability(str, Enum):
    EXACT_MATCH = "exact_match"
    INVARIANT_PRESERVING = "invariant_preserving"
    STATISTICALLY_BOUNDED = "statistically_bounded"


class EvidenceDeterminism(str, Enum):
    DETERMINISTIC = "deterministic"
    SAMPLED = "sampled"
    EXTERNAL = "external"


class EntropySource(str, Enum):
    SEEDED_RNG = "seeded_rng"
    EXTERNAL_ORACLE = "external_oracle"
    HUMAN_INPUT = "human_input"
    DATA = "data"


class EntropyMagnitude(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationRandomness(str, Enum):
    DETERMINISTIC = "deterministic"
    SAMPLED = "sampled"
    STATISTICAL = "statistical"


class ReasonCode(str, Enum):
    CONTRADICTION_DETECTED = "contradiction_detected"


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
    "CausalityTag",
    "EventType",
    "StepType",
    "VerificationPhase",
    "ArbitrationRule",
    "DeterminismLevel",
    "DeterminismClass",
    "FlowState",
    "DatasetState",
    "ReplayAcceptability",
    "EvidenceDeterminism",
    "EntropySource",
    "EntropyMagnitude",
    "ReasonCode",
    "VerificationRandomness",
]
