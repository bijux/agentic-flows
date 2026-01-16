import hashlib
from typing import Any, List

import bijux_rag
import bijux_vex

from agentic_flows.spec.retrieval_request import RetrievalRequest
from agentic_flows.spec.retrieved_evidence import RetrievedEvidence


class RetrievalExecutor:
    def execute(self, request: RetrievalRequest) -> List[RetrievedEvidence]:
        if not hasattr(bijux_rag, "retrieve"):
            raise RuntimeError("bijux_rag.retrieve is required for retrieval")
        if not hasattr(bijux_vex, "enforce_contract"):
            raise RuntimeError("bijux_vex.enforce_contract is required for enforcement")

        raw_evidence = bijux_rag.retrieve(
            query=request.query,
            top_k=request.top_k,
            scope=request.scope,
            vector_contract_id=request.vector_contract_id,
        )

        evidence = self._normalize_evidence(raw_evidence)
        if not evidence:
            raise ValueError("retrieval returned no evidence")

        if any(item.vector_contract_id != request.vector_contract_id for item in evidence):
            raise ValueError("retrieval evidence vector contract mismatch")

        if not bijux_vex.enforce_contract(request.vector_contract_id, evidence):
            raise ValueError("retrieval evidence failed vector contract enforcement")

        return evidence

    def _normalize_evidence(self, raw: Any) -> List[RetrievedEvidence]:
        if not isinstance(raw, list):
            raise ValueError("retrieval results must be a list")

        evidence: List[RetrievedEvidence] = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise ValueError("retrieval evidence must be dict entries")
            if "evidence_id" not in entry or "source_uri" not in entry or "content" not in entry:
                raise ValueError("retrieval evidence missing required fields")
            content_hash = self._hash_content(entry["content"])
            evidence.append(
                RetrievedEvidence(
                    evidence_id=str(entry["evidence_id"]),
                    source_uri=str(entry["source_uri"]),
                    content_hash=content_hash,
                    score=float(entry.get("score", 0.0)),
                    vector_contract_id=str(entry.get("vector_contract_id", "")),
                )
            )
        return evidence

    @staticmethod
    def _hash_content(content: Any) -> str:
        payload = str(content).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
