# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for spec/model/__init__.py."""

from __future__ import annotations

import importlib
import sys
import types

from agentic_flows.spec.model.artifact.artifact import Artifact
from agentic_flows.spec.model.artifact.entropy_budget import EntropyBudget
from agentic_flows.spec.model.artifact.entropy_usage import EntropyUsage
from agentic_flows.spec.model.artifact.non_determinism_source import (
    NonDeterminismSource,
)
from agentic_flows.spec.model.artifact.reasoning_claim import ReasoningClaim
from agentic_flows.spec.model.artifact.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.model.datasets.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.datasets.retrieval_request import RetrievalRequest
from agentic_flows.spec.model.execution.execution_plan import ExecutionPlan
from agentic_flows.spec.model.execution.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution.execution_trace import ExecutionTrace
from agentic_flows.spec.model.execution.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.execution.resolved_step import ResolvedStep
from agentic_flows.spec.model.flow_manifest import FlowManifest
from agentic_flows.spec.model.identifiers.agent_invocation import AgentInvocation
from agentic_flows.spec.model.identifiers.execution_event import ExecutionEvent
from agentic_flows.spec.model.identifiers.tool_invocation import ToolInvocation
from agentic_flows.spec.model.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.model.reasoning_step import ReasoningStep
from agentic_flows.spec.model.verification.arbitration_policy import ArbitrationPolicy
from agentic_flows.spec.model.verification.verification import VerificationPolicy
from agentic_flows.spec.model.verification.verification_arbitration import (
    VerificationArbitration,
)
from agentic_flows.spec.model.verification.verification_result import (
    VerificationResult,
)
from agentic_flows.spec.model.verification.verification_rule import VerificationRule


def _alias_module(old: str, new: str) -> None:
    """Internal helper; not part of the public API."""
    module = types.ModuleType(old)
    attr_name = old.rsplit(".", 1)[-1]

    def _load_target():
        """Internal helper; not part of the public API."""
        target = importlib.import_module(new)
        sys.modules[old] = target
        setattr(sys.modules[__name__], attr_name, target)
        return target

    def _module_getattr(name: str) -> object:
        """Internal helper; not part of the public API."""
        target = _load_target()
        return getattr(target, name)

    def _module_dir() -> list[str]:
        """Internal helper; not part of the public API."""
        target = _load_target()
        return list(dir(target))

    def _module_setattr(name: str, value: object) -> None:
        """Internal helper; not part of the public API."""
        target = _load_target()
        setattr(target, name, value)

    module.__getattr__ = _module_getattr  # type: ignore[attr-defined]
    module.__dir__ = _module_dir  # type: ignore[attr-defined]
    module.__setattr__ = _module_setattr  # type: ignore[attr-defined]
    sys.modules[old] = module
    setattr(sys.modules[__name__], attr_name, module)


_alias_module(
    "agentic_flows.spec.model.agent_invocation",
    "agentic_flows.spec.model.identifiers.agent_invocation",
)
_alias_module(
    "agentic_flows.spec.model.tool_invocation",
    "agentic_flows.spec.model.identifiers.tool_invocation",
)
_alias_module(
    "agentic_flows.spec.model.execution_event",
    "agentic_flows.spec.model.identifiers.execution_event",
)
_alias_module(
    "agentic_flows.spec.model.execution_plan",
    "agentic_flows.spec.model.execution.execution_plan",
)
_alias_module(
    "agentic_flows.spec.model.execution_steps",
    "agentic_flows.spec.model.execution.execution_steps",
)
_alias_module(
    "agentic_flows.spec.model.resolved_step",
    "agentic_flows.spec.model.execution.resolved_step",
)
_alias_module(
    "agentic_flows.spec.model.execution_trace",
    "agentic_flows.spec.model.execution.execution_trace",
)
_alias_module(
    "agentic_flows.spec.model.replay_envelope",
    "agentic_flows.spec.model.execution.replay_envelope",
)
_alias_module(
    "agentic_flows.spec.model.artifact",
    "agentic_flows.spec.model.artifact.artifact",
)
_alias_module(
    "agentic_flows.spec.model.retrieved_evidence",
    "agentic_flows.spec.model.artifact.retrieved_evidence",
)
_alias_module(
    "agentic_flows.spec.model.reasoning_claim",
    "agentic_flows.spec.model.artifact.reasoning_claim",
)
_alias_module(
    "agentic_flows.spec.model.entropy_usage",
    "agentic_flows.spec.model.artifact.entropy_usage",
)
_alias_module(
    "agentic_flows.spec.model.entropy_budget",
    "agentic_flows.spec.model.artifact.entropy_budget",
)
_alias_module(
    "agentic_flows.spec.model.non_determinism_source",
    "agentic_flows.spec.model.artifact.non_determinism_source",
)
_alias_module(
    "agentic_flows.spec.model.verification",
    "agentic_flows.spec.model.verification.verification",
)
_alias_module(
    "agentic_flows.spec.model.verification_rule",
    "agentic_flows.spec.model.verification.verification_rule",
)
_alias_module(
    "agentic_flows.spec.model.verification_result",
    "agentic_flows.spec.model.verification.verification_result",
)
_alias_module(
    "agentic_flows.spec.model.verification_arbitration",
    "agentic_flows.spec.model.verification.verification_arbitration",
)
_alias_module(
    "agentic_flows.spec.model.arbitration_policy",
    "agentic_flows.spec.model.verification.arbitration_policy",
)
_alias_module(
    "agentic_flows.spec.model.dataset_descriptor",
    "agentic_flows.spec.model.datasets.dataset_descriptor",
)
_alias_module(
    "agentic_flows.spec.model.retrieval_request",
    "agentic_flows.spec.model.datasets.retrieval_request",
)

__all__ = [
    "AgentInvocation",
    "Artifact",
    "ArbitrationPolicy",
    "ExecutionEvent",
    "DatasetDescriptor",
    "ExecutionPlan",
    "ExecutionSteps",
    "ExecutionTrace",
    "EntropyBudget",
    "EntropyUsage",
    "FlowManifest",
    "NonDeterminismSource",
    "ReplayEnvelope",
    "ReasoningBundle",
    "ReasoningClaim",
    "ReasoningStep",
    "ResolvedStep",
    "RetrievalRequest",
    "RetrievedEvidence",
    "ToolInvocation",
    "VerificationPolicy",
    "VerificationArbitration",
    "VerificationResult",
    "VerificationRule",
]
