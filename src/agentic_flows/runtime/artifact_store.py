# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.ontology.ids import ArtifactID, ContentHash
from agentic_flows.spec.ontology.ontology import ArtifactScope, ArtifactType


class ArtifactStore(ABC):
    @abstractmethod
    def create(
        self,
        *,
        spec_version: str,
        artifact_id: ArtifactID,
        artifact_type: ArtifactType,
        producer: str,
        parent_artifacts: tuple[ArtifactID, ...],
        content_hash: ContentHash,
        scope: ArtifactScope,
    ) -> Artifact:
        raise NotImplementedError

    @abstractmethod
    def save(self, artifact: Artifact) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, artifact_id: ArtifactID) -> Artifact:
        raise NotImplementedError


class InMemoryArtifactStore(ArtifactStore):
    def __init__(self) -> None:
        self._items: dict[ArtifactID, Artifact] = {}

    def create(
        self,
        *,
        spec_version: str,
        artifact_id: ArtifactID,
        artifact_type: ArtifactType,
        producer: str,
        parent_artifacts: tuple[ArtifactID, ...],
        content_hash: ContentHash,
        scope: ArtifactScope,
    ) -> Artifact:
        artifact = Artifact(
            spec_version=spec_version,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            producer=producer,
            parent_artifacts=parent_artifacts,
            content_hash=content_hash,
            scope=scope,
        )
        self.save(artifact)
        return artifact

    def save(self, artifact: Artifact) -> None:
        existing = self._items.get(artifact.artifact_id)
        if existing is not None and existing.scope is ArtifactScope.AUDIT:
            raise ValueError("AUDIT artifacts cannot be overwritten")
        self._items[artifact.artifact_id] = artifact

    def load(self, artifact_id: ArtifactID) -> Artifact:
        if artifact_id not in self._items:
            raise KeyError(f"Artifact not found: {artifact_id}")
        return self._items[artifact_id]
