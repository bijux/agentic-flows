# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal

from agentic_flows.spec.ids import ArtifactID, ContentHash
from agentic_flows.spec.ontology import ArtifactType

_ALLOW_ARTIFACT_CREATE: ContextVar[bool] = ContextVar(
    "allow_artifact_create", default=False
)


def _allow_artifact_creation() -> ContextVar[bool]:
    return _ALLOW_ARTIFACT_CREATE


@dataclass
class Artifact:
    spec_version: str
    artifact_id: ArtifactID
    artifact_type: ArtifactType
    producer: Literal["agent", "retrieval", "reasoning"]
    parent_artifacts: tuple[ArtifactID, ...]
    content_hash: ContentHash

    def __post_init__(self) -> None:
        if not _ALLOW_ARTIFACT_CREATE.get():
            raise RuntimeError("Artifacts must be created via ArtifactStore")


__all__ = ["Artifact"]
