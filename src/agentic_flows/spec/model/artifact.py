# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agentic_flows.spec.ontology.ids import ArtifactID, ContentHash, TenantID
from agentic_flows.spec.ontology.ontology import ArtifactScope, ArtifactType


@dataclass(frozen=True)
class Artifact:
    spec_version: str
    artifact_id: ArtifactID
    tenant_id: TenantID
    artifact_type: ArtifactType
    producer: Literal["agent", "retrieval", "reasoning"]
    parent_artifacts: tuple[ArtifactID, ...]
    content_hash: ContentHash
    scope: ArtifactScope


__all__ = ["Artifact"]
