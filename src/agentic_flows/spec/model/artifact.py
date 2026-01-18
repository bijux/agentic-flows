# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agentic_flows.spec.ontology.ids import ArtifactID, ContentHash
from agentic_flows.spec.ontology.ontology import ArtifactType


@dataclass(frozen=True)
class Artifact:
    spec_version: str
    artifact_id: ArtifactID
    artifact_type: ArtifactType
    producer: Literal["agent", "retrieval", "reasoning"]
    parent_artifacts: tuple[ArtifactID, ...]
    content_hash: ContentHash


__all__ = ["Artifact"]
