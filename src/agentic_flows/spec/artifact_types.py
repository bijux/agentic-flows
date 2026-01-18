# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from enum import Enum


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


__all__ = ["ArtifactType"]
