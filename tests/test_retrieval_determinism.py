# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import bijux_rag
import bijux_vex

from agentic_flows.runtime.retrieval_executor import RetrievalExecutor
from agentic_flows.spec.retrieval_request import RetrievalRequest
from agentic_flows.spec.ids import ContractID, RequestID


def test_retrieval_determinism() -> None:
    request = RetrievalRequest(
        spec_version="v1",
        request_id=RequestID("req-1"),
        query="what is bijux",
        vector_contract_id=ContractID("contract-1"),
        top_k=2,
        scope="project",
    )

    def _deterministic_retrieve(**_kwargs):
        return [
            {
                "evidence_id": "ev-1",
                "source_uri": "file://doc-1",
                "content": "alpha",
                "score": 0.9,
                "vector_contract_id": "contract-1",
            },
            {
                "evidence_id": "ev-2",
                "source_uri": "file://doc-2",
                "content": "beta",
                "score": 0.8,
                "vector_contract_id": "contract-1",
            },
        ]

    bijux_rag.retrieve = _deterministic_retrieve
    bijux_vex.enforce_contract = lambda *_args, **_kwargs: True

    executor = RetrievalExecutor()
    evidence_one = executor.execute(request)
    evidence_two = executor.execute(request)

    assert [(item.evidence_id, item.content_hash) for item in evidence_one] == [
        (item.evidence_id, item.content_hash) for item in evidence_two
    ]
