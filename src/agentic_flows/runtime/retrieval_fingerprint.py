# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.spec.retrieval_request import RetrievalRequest


def fingerprint_retrieval(request: RetrievalRequest) -> str:
    payload = {
        "request_id": request.request_id,
        "query": request.query,
        "vector_contract_id": request.vector_contract_id,
        "top_k": request.top_k,
        "scope": request.scope,
    }
    return fingerprint_inputs(payload)
