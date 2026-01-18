# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib
from typing import Any

import bijux_rag
import bijux_vex

from agentic_flows.spec.model.retrieval_request import RetrievalRequest
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
from agentic_flows.spec.ontology.ids import ContentHash, ContractID, EvidenceID


class RetrievalExecutor:
    def execute(self, request: RetrievalRequest) -> list[RetrievedEvidence]:
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

        if any(
            item.vector_contract_id != request.vector_contract_id for item in evidence
        ):
            raise ValueError("retrieval evidence vector contract mismatch")

        if not bijux_vex.enforce_contract(request.vector_contract_id, evidence):
            raise ValueError("retrieval evidence failed vector contract enforcement")

        return evidence

    def _normalize_evidence(self, raw: Any) -> list[RetrievedEvidence]:
        if not isinstance(raw, list):
            raise ValueError("retrieval results must be a list")

        evidence: list[RetrievedEvidence] = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise ValueError("retrieval evidence must be dict entries")
            if (
                "evidence_id" not in entry
                or "source_uri" not in entry
                or "content" not in entry
            ):
                raise ValueError("retrieval evidence missing required fields")
            content_hash = ContentHash(self._hash_content(entry["content"]))
            evidence.append(
                RetrievedEvidence(
                    spec_version="v1",
                    evidence_id=EvidenceID(str(entry["evidence_id"])),
                    source_uri=str(entry["source_uri"]),
                    content_hash=content_hash,
                    score=float(entry.get("score", 0.0)),
                    vector_contract_id=ContractID(
                        str(entry.get("vector_contract_id", ""))
                    ),
                )
            )
        return evidence

    @staticmethod
    def _hash_content(content: Any) -> str:
        payload = str(content).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
