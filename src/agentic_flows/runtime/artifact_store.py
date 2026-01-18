# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.ids import ArtifactID


class ArtifactStore(ABC):
    @abstractmethod
    def save(self, artifact: Artifact) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, artifact_id: ArtifactID) -> Artifact:
        raise NotImplementedError
