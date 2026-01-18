# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ids import AgentID, BundleID, EvidenceID
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep


@dataclass(frozen=True)
class ReasoningBundle:
    spec_version: str
    bundle_id: BundleID
    claims: tuple[ReasoningClaim, ...]
    steps: tuple[ReasoningStep, ...]
    evidence_ids: tuple[EvidenceID, ...]
    producer_agent_id: AgentID


__all__ = ["ReasoningBundle"]
