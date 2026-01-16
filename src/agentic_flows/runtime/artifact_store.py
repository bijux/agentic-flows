from abc import ABC, abstractmethod

from agentic_flows.spec.artifact import Artifact


class ArtifactStore(ABC):
    @abstractmethod
    def save(self, artifact: Artifact) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, artifact_id: str) -> Artifact:
        raise NotImplementedError
