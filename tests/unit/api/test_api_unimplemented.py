# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from fastapi.testclient import TestClient

from agentic_flows.http_api.app import app


def test_run_flow_unimplemented() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/flows/run",
        json={
            "flow_manifest": "file://manifest.json",
            "inputs_fingerprint": "inputs-hash",
            "run_mode": "live",
            "dataset_id": "dataset-1",
            "policy_fingerprint": "policy-hash",
        },
        headers={
            "X-Agentic-Gate": "gate-1",
            "X-Determinism-Level": "strict",
            "X-Policy-Fingerprint": "policy-hash",
        },
    )
    assert response.status_code == 501
    payload = response.json()
    assert payload["failure_class"] == "structural"
    assert payload["violated_contract"] == "not_implemented"


def test_replay_flow_unimplemented() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/flows/replay",
        json={
            "run_id": "run-1",
            "expected_plan_hash": "plan-hash",
            "acceptability_threshold": "exact_match",
            "observer_mode": False,
        },
        headers={
            "X-Agentic-Gate": "gate-1",
            "X-Determinism-Level": "strict",
            "X-Policy-Fingerprint": "policy-hash",
        },
    )
    assert response.status_code == 501
    payload = response.json()
    assert payload["failure_class"] == "structural"
    assert payload["violated_contract"] == "not_implemented"
