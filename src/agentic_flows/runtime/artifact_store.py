# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib

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
        if existing is not None:
            raise ValueError("Artifact IDs must be unique per run")
        self._items[artifact.artifact_id] = artifact

    def load(self, artifact_id: ArtifactID) -> Artifact:
        if artifact_id not in self._items:
            raise KeyError(f"Artifact not found: {artifact_id}")
        return self._items[artifact_id]


class HostileArtifactStore(ArtifactStore):
    def __init__(
        self,
        *,
        seed: int,
        max_delay: int = 2,
        drop_rate: float = 0.2,
        corruption_rate: float = 0.2,
    ) -> None:
        self._seed = seed
        self._max_delay = max_delay
        self._drop_rate = drop_rate
        self._corruption_rate = corruption_rate
        self._items: dict[ArtifactID, Artifact] = {}
        self._pending: dict[ArtifactID, tuple[Artifact, int]] = {}

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
        if existing is not None:
            raise ValueError("Artifact IDs must be unique per run")
        decision = self._decision(artifact.artifact_id)
        if decision["drop"]:
            return
        stored = artifact
        if decision["corrupt"]:
            stored = Artifact(
                spec_version=artifact.spec_version,
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                producer=artifact.producer,
                parent_artifacts=artifact.parent_artifacts,
                content_hash=ContentHash(
                    self._hash_payload(f"corrupt:{artifact.content_hash}")
                ),
                scope=artifact.scope,
            )
        if decision["delay"] > 0:
            self._pending[artifact.artifact_id] = (stored, decision["delay"])
            return
        self._items[artifact.artifact_id] = stored

    def load(self, artifact_id: ArtifactID) -> Artifact:
        self._tick()
        if artifact_id in self._pending:
            artifact, delay = self._pending[artifact_id]
            if delay > 0:
                self._pending[artifact_id] = (artifact, delay - 1)
                raise KeyError(f"Artifact not yet visible: {artifact_id}")
            self._items[artifact_id] = artifact
            self._pending.pop(artifact_id, None)
        if artifact_id not in self._items:
            raise KeyError(f"Artifact not found: {artifact_id}")
        return self._items[artifact_id]

    def _tick(self) -> None:
        for artifact_id, (artifact, delay) in list(self._pending.items()):
            if delay <= 0:
                self._items[artifact_id] = artifact
                self._pending.pop(artifact_id, None)

    def _decision(self, artifact_id: ArtifactID) -> dict[str, object]:
        payload = f"{self._seed}:{artifact_id}"
        digest = self._hash_payload(payload)
        bucket = int(digest[:8], 16) % 100
        drop = bucket < int(self._drop_rate * 100)
        corrupt = not drop and bucket < int(self._drop_rate * 100) + int(
            self._corruption_rate * 100
        )
        delay = 0
        if not drop:
            delay = int(digest[8:16], 16) % (self._max_delay + 1)
        return {"drop": drop, "corrupt": corrupt, "delay": delay}

    @staticmethod
    def _hash_payload(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
