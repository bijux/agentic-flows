from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalRequest:
    request_id: str
    query: str
    vector_contract_id: str
    top_k: int
    scope: str


__all__ = ["RetrievalRequest"]
