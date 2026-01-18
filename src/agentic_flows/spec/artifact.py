# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agentic_flows.spec.artifact_types import ArtifactType
from agentic_flows.spec.ids import ArtifactID, ContentHash


@dataclass
class Artifact:
    spec_version: str
    artifact_id: ArtifactID
    artifact_type: ArtifactType
    producer: Literal["agent", "retrieval", "reasoning"]
    parent_artifacts: tuple[ArtifactID, ...]
    content_hash: ContentHash


__all__ = ["Artifact"]
