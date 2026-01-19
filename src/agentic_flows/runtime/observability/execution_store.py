# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import duckdb

from agentic_flows.spec.contracts.dataset_contract import validate_transition
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.ontology.ids import (
    ClaimID,
    ContentHash,
    DatasetID,
    EnvironmentFingerprint,
    FlowID,
    PlanHash,
    PolicyFingerprint,
    ResolverID,
    TenantID,
    ToolID,
)
from agentic_flows.spec.ontology.ontology import (
    DatasetState,
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    EventType,
    FlowState,
    ReplayAcceptability,
)

SCHEMA_VERSION = 1


class DuckDBExecutionStore:
    def __init__(self, path: Path) -> None:
        self._connection = duckdb.connect(str(path))
        self._migrate()

    def save_trace(self, trace: ExecutionTrace) -> None:
        payload = json.dumps(_encode_trace(trace))
        self._connection.execute(
            """
            INSERT OR REPLACE INTO traces (flow_id, tenant_id, trace_json)
            VALUES (?, ?, ?)
            """,
            (str(trace.flow_id), str(trace.tenant_id), payload),
        )
        self._connection.commit()

    def load_trace(self, flow_id: FlowID, *, tenant_id: TenantID) -> ExecutionTrace:
        row = self._connection.execute(
            "SELECT trace_json FROM traces WHERE flow_id = ? AND tenant_id = ?",
            (str(flow_id), str(tenant_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Trace not found: {flow_id}")
        return _decode_trace(json.loads(row[0]))

    def save_entropy_usage(
        self, flow_id: FlowID, tenant_id: TenantID, usage: tuple[EntropyUsage, ...]
    ) -> None:
        payload = json.dumps([_encode_entropy_usage(item) for item in usage])
        self._connection.execute(
            """
            INSERT OR REPLACE INTO entropy_usage (flow_id, tenant_id, usage_json)
            VALUES (?, ?, ?)
            """,
            (str(flow_id), str(tenant_id), payload),
        )
        self._connection.commit()

    def load_entropy_usage(
        self, flow_id: FlowID, *, tenant_id: TenantID
    ) -> tuple[EntropyUsage, ...]:
        row = self._connection.execute(
            "SELECT usage_json FROM entropy_usage WHERE flow_id = ? AND tenant_id = ?",
            (str(flow_id), str(tenant_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Entropy usage not found: {flow_id}")
        payload = json.loads(row[0])
        return tuple(_decode_entropy_usage(item) for item in payload)

    def save_replay_envelope(
        self, flow_id: FlowID, tenant_id: TenantID, envelope: ReplayEnvelope
    ) -> None:
        payload = json.dumps(_encode_envelope(envelope))
        self._connection.execute(
            """
            INSERT OR REPLACE INTO replay_envelopes (flow_id, tenant_id, envelope_json)
            VALUES (?, ?, ?)
            """,
            (str(flow_id), str(tenant_id), payload),
        )
        self._connection.commit()

    def load_replay_envelope(
        self, flow_id: FlowID, *, tenant_id: TenantID
    ) -> ReplayEnvelope:
        row = self._connection.execute(
            "SELECT envelope_json FROM replay_envelopes WHERE flow_id = ? AND tenant_id = ?",
            (str(flow_id), str(tenant_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Replay envelope not found: {flow_id}")
        return _decode_envelope(json.loads(row[0]))

    def save_dataset_descriptor(self, dataset: DatasetDescriptor) -> None:
        row = self._connection.execute(
            """
            SELECT dataset_state FROM datasets
            WHERE tenant_id = ? AND dataset_id = ?
            """,
            (str(dataset.tenant_id), str(dataset.dataset_id)),
        ).fetchone()
        previous_state: DatasetState | None = None
        if row is not None:
            previous_state = DatasetState(row[0])
        validate_transition(previous_state, dataset.dataset_state)
        payload = json.dumps(_encode_dataset(dataset))
        self._connection.execute(
            """
            INSERT OR REPLACE INTO datasets
            (tenant_id, dataset_id, dataset_state, dataset_version, dataset_hash, dataset_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(dataset.tenant_id),
                str(dataset.dataset_id),
                dataset.dataset_state.value,
                dataset.dataset_version,
                dataset.dataset_hash,
                payload,
            ),
        )
        self._connection.commit()

    def load_dataset_descriptor(
        self, dataset_id: DatasetID, *, tenant_id: TenantID
    ) -> DatasetDescriptor:
        row = self._connection.execute(
            """
            SELECT dataset_json FROM datasets
            WHERE tenant_id = ? AND dataset_id = ?
            """,
            (str(tenant_id), str(dataset_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Dataset not found: {dataset_id}")
        return _decode_dataset(json.loads(row[0]))

    def save_entropy_snapshot(
        self, flow_id: FlowID, tenant_id: TenantID, snapshot: dict[str, object]
    ) -> None:
        payload = json.dumps(snapshot)
        self._connection.execute(
            """
            INSERT OR REPLACE INTO entropy_snapshots (flow_id, tenant_id, snapshot_json)
            VALUES (?, ?, ?)
            """,
            (str(flow_id), str(tenant_id), payload),
        )
        self._connection.commit()

    def load_entropy_snapshot(
        self, flow_id: FlowID, *, tenant_id: TenantID
    ) -> dict[str, object]:
        row = self._connection.execute(
            "SELECT snapshot_json FROM entropy_snapshots WHERE flow_id = ? AND tenant_id = ?",
            (str(flow_id), str(tenant_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Entropy snapshot not found: {flow_id}")
        return json.loads(row[0])

    def save_outcome_snapshot(
        self, flow_id: FlowID, tenant_id: TenantID, snapshot: dict[str, object]
    ) -> None:
        payload = json.dumps(snapshot)
        self._connection.execute(
            """
            INSERT OR REPLACE INTO outcome_snapshots (flow_id, tenant_id, snapshot_json)
            VALUES (?, ?, ?)
            """,
            (str(flow_id), str(tenant_id), payload),
        )
        self._connection.commit()

    def load_outcome_snapshot(
        self, flow_id: FlowID, *, tenant_id: TenantID
    ) -> dict[str, object]:
        row = self._connection.execute(
            "SELECT snapshot_json FROM outcome_snapshots WHERE flow_id = ? AND tenant_id = ?",
            (str(flow_id), str(tenant_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Outcome snapshot not found: {flow_id}")
        return json.loads(row[0])

    def _migrate(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        row = self._connection.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()
        current = int(row[0] or 0)
        for version, statement in _MIGRATIONS:
            if version > current:
                self._connection.execute(statement)
                self._connection.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, "now"),
                )
        self._connection.commit()


_MIGRATIONS = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS traces (
            flow_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            trace_json TEXT NOT NULL,
            PRIMARY KEY (flow_id, tenant_id)
        );
        CREATE TABLE IF NOT EXISTS entropy_usage (
            flow_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            usage_json TEXT NOT NULL,
            PRIMARY KEY (flow_id, tenant_id)
        );
        CREATE TABLE IF NOT EXISTS replay_envelopes (
            flow_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            envelope_json TEXT NOT NULL,
            PRIMARY KEY (flow_id, tenant_id)
        );
        CREATE TABLE IF NOT EXISTS datasets (
            tenant_id TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            dataset_state TEXT NOT NULL,
            dataset_version TEXT NOT NULL,
            dataset_hash TEXT NOT NULL,
            dataset_json TEXT NOT NULL,
            PRIMARY KEY (tenant_id, dataset_id)
        );
        CREATE TABLE IF NOT EXISTS entropy_snapshots (
            flow_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            PRIMARY KEY (flow_id, tenant_id)
        );
        CREATE TABLE IF NOT EXISTS outcome_snapshots (
            flow_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            PRIMARY KEY (flow_id, tenant_id)
        );
        """,
    ),
)


def _encode_trace(trace: ExecutionTrace) -> dict[str, Any]:
    payload = asdict(trace)
    payload["flow_id"] = str(trace.flow_id)
    payload["tenant_id"] = str(trace.tenant_id)
    payload["parent_flow_id"] = (
        str(trace.parent_flow_id) if trace.parent_flow_id is not None else None
    )
    payload["child_flow_ids"] = [str(item) for item in trace.child_flow_ids]
    payload["flow_state"] = trace.flow_state.value
    payload["determinism_level"] = trace.determinism_level.value
    payload["replay_acceptability"] = trace.replay_acceptability.value
    payload["dataset"] = _encode_dataset(trace.dataset)
    payload["replay_envelope"] = _encode_envelope(trace.replay_envelope)
    payload["allow_deprecated_datasets"] = trace.allow_deprecated_datasets
    payload["environment_fingerprint"] = str(trace.environment_fingerprint)
    payload["plan_hash"] = str(trace.plan_hash)
    payload["verification_policy_fingerprint"] = (
        str(trace.verification_policy_fingerprint)
        if trace.verification_policy_fingerprint is not None
        else None
    )
    payload["resolver_id"] = str(trace.resolver_id)
    payload["events"] = [_encode_event(event) for event in trace.events]
    payload["tool_invocations"] = [
        _encode_tool_invocation(item) for item in trace.tool_invocations
    ]
    payload["entropy_usage"] = [
        _encode_entropy_usage(item) for item in trace.entropy_usage
    ]
    payload["claim_ids"] = [str(item) for item in trace.claim_ids]
    return payload


def _decode_trace(payload: dict[str, Any]) -> ExecutionTrace:
    return ExecutionTrace(
        spec_version=payload["spec_version"],
        flow_id=FlowID(payload["flow_id"]),
        tenant_id=TenantID(payload["tenant_id"]),
        parent_flow_id=FlowID(payload["parent_flow_id"])
        if payload["parent_flow_id"]
        else None,
        child_flow_ids=tuple(FlowID(item) for item in payload["child_flow_ids"]),
        flow_state=FlowState(payload["flow_state"]),
        determinism_level=DeterminismLevel(payload["determinism_level"]),
        replay_acceptability=ReplayAcceptability(payload["replay_acceptability"]),
        dataset=_decode_dataset(payload["dataset"]),
        replay_envelope=_decode_envelope(payload["replay_envelope"]),
        allow_deprecated_datasets=bool(payload["allow_deprecated_datasets"]),
        environment_fingerprint=EnvironmentFingerprint(
            payload["environment_fingerprint"]
        ),
        plan_hash=PlanHash(payload["plan_hash"]),
        verification_policy_fingerprint=PolicyFingerprint(
            payload["verification_policy_fingerprint"]
        )
        if payload["verification_policy_fingerprint"] is not None
        else None,
        resolver_id=ResolverID(payload["resolver_id"]),
        events=tuple(_decode_event(item) for item in payload["events"]),
        tool_invocations=tuple(
            _decode_tool_invocation(item) for item in payload["tool_invocations"]
        ),
        entropy_usage=tuple(
            _decode_entropy_usage(item) for item in payload["entropy_usage"]
        ),
        claim_ids=tuple(ClaimID(item) for item in payload["claim_ids"]),
        contradiction_count=int(payload["contradiction_count"]),
        arbitration_decision=payload["arbitration_decision"],
        finalized=bool(payload["finalized"]),
    )


def _encode_event(event: ExecutionEvent) -> dict[str, Any]:
    payload = asdict(event)
    payload["event_type"] = event.event_type.value
    payload["payload_hash"] = str(event.payload_hash)
    return payload


def _decode_event(payload: dict[str, Any]) -> ExecutionEvent:
    return ExecutionEvent(
        spec_version=payload["spec_version"],
        event_index=int(payload["event_index"]),
        step_index=int(payload["step_index"]),
        event_type=EventType(payload["event_type"]),
        timestamp_utc=payload["timestamp_utc"],
        payload=payload["payload"],
        payload_hash=ContentHash(payload["payload_hash"]),
    )


def _encode_tool_invocation(item: ToolInvocation) -> dict[str, Any]:
    payload = asdict(item)
    payload["tool_id"] = str(item.tool_id)
    payload["determinism_level"] = item.determinism_level.value
    payload["inputs_fingerprint"] = str(item.inputs_fingerprint)
    payload["outputs_fingerprint"] = (
        str(item.outputs_fingerprint) if item.outputs_fingerprint is not None else None
    )
    return payload


def _decode_tool_invocation(payload: dict[str, Any]) -> ToolInvocation:
    return ToolInvocation(
        spec_version=payload["spec_version"],
        tool_id=ToolID(payload["tool_id"]),
        determinism_level=DeterminismLevel(payload["determinism_level"]),
        inputs_fingerprint=ContentHash(payload["inputs_fingerprint"]),
        outputs_fingerprint=ContentHash(payload["outputs_fingerprint"])
        if payload["outputs_fingerprint"] is not None
        else None,
        duration=float(payload["duration"]),
        outcome=payload["outcome"],
    )


def _encode_entropy_usage(item: EntropyUsage) -> dict[str, Any]:
    return {
        "spec_version": item.spec_version,
        "tenant_id": str(item.tenant_id),
        "source": item.source.value,
        "magnitude": item.magnitude.value,
        "description": item.description,
        "step_index": item.step_index,
    }


def _decode_entropy_usage(payload: dict[str, Any]) -> EntropyUsage:
    return EntropyUsage(
        spec_version=payload["spec_version"],
        tenant_id=TenantID(payload["tenant_id"]),
        source=EntropySource(payload["source"]),
        magnitude=EntropyMagnitude(payload["magnitude"]),
        description=payload["description"],
        step_index=payload["step_index"],
    )


def _encode_envelope(envelope: ReplayEnvelope) -> dict[str, Any]:
    return {
        "spec_version": envelope.spec_version,
        "min_claim_overlap": envelope.min_claim_overlap,
        "max_contradiction_delta": envelope.max_contradiction_delta,
        "require_same_arbitration": envelope.require_same_arbitration,
    }


def _decode_envelope(payload: dict[str, Any]) -> ReplayEnvelope:
    return ReplayEnvelope(
        spec_version=payload["spec_version"],
        min_claim_overlap=float(payload["min_claim_overlap"]),
        max_contradiction_delta=int(payload["max_contradiction_delta"]),
        require_same_arbitration=bool(payload["require_same_arbitration"]),
    )


def _encode_dataset(dataset: DatasetDescriptor) -> dict[str, Any]:
    return {
        "spec_version": dataset.spec_version,
        "dataset_id": str(dataset.dataset_id),
        "tenant_id": str(dataset.tenant_id),
        "dataset_version": dataset.dataset_version,
        "dataset_hash": dataset.dataset_hash,
        "dataset_state": dataset.dataset_state.value,
    }


def _decode_dataset(payload: dict[str, Any]) -> DatasetDescriptor:
    return DatasetDescriptor(
        spec_version=payload["spec_version"],
        dataset_id=DatasetID(payload["dataset_id"]),
        tenant_id=TenantID(payload["tenant_id"]),
        dataset_version=payload["dataset_version"],
        dataset_hash=payload["dataset_hash"],
        dataset_state=DatasetState(payload["dataset_state"]),
    )


__all__ = ["DuckDBExecutionStore", "SCHEMA_VERSION"]
