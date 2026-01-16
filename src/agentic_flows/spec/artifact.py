from dataclasses import dataclass
from typing import Literal, Tuple


@dataclass
class Artifact:
    artifact_id: str
    artifact_type: str
    producer: Literal["agent", "retrieval", "reasoning"]
    parent_artifacts: Tuple[str, ...]
    content_hash: str


__all__ = ["Artifact"]
