from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedEvidence:
    evidence_id: str
    source_uri: str
    content_hash: str
    score: float
    vector_contract_id: str


__all__ = ["RetrievedEvidence"]
