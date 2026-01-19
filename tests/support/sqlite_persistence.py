# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from typing import Any

from agentic_flows.runtime.artifact_store import ArtifactStore
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.tool_invocation import ToolInvocation
from agentic_flows.spec.ontology.ids import (
    ArtifactID,
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
    ArtifactScope,
    ArtifactType,
    DeterminismLevel,
    EntropyMagnitude,
    EntropySource,
    EventType,
    ReplayAcceptability,
    DatasetState,
)


class SqliteMigrator:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def migrate(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        current = self._current_version()
        for version, statement in _MIGRATIONS:
            if version > current:
                self._connection.executescript(statement)
                self._connection.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, "now"),
                )
        self._connection.commit()

    def _current_version(self) -> int:
        cursor = self._connection.execute("SELECT MAX(version) FROM schema_migrations")
        row = cursor.fetchone()
        return int(row[0] or 0)


_MIGRATIONS = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id TEXT PRIMARY KEY,
            spec_version TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            producer TEXT NOT NULL,
            parent_artifacts TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            scope TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS traces (
            flow_id TEXT PRIMARY KEY,
            trace_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entropy_usage (
            flow_id TEXT NOT NULL,
            entry_index INTEGER NOT NULL,
            spec_version TEXT NOT NULL,
            source TEXT NOT NULL,
            magnitude TEXT NOT NULL,
            description TEXT NOT NULL,
            step_index INTEGER,
            PRIMARY KEY (flow_id, entry_index)
        );
        """,
    ),
)


class SqliteArtifactStore(ArtifactStore):
    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path)
        SqliteMigrator(self._connection).migrate()

    def create(
        self,
        *,
        spec_version: str,
        artifact_id: ArtifactID,
        artifact_type: ArtifactType,
        producer: str,
        parent_artifacts: tuple[ArtifactID, ...],
        content_hash: ContentHash,
        scope: ArtifactScope,
    ) -> Artifact:
        artifact = Artifact(
            spec_version=spec_version,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            producer=producer,
            parent_artifacts=parent_artifacts,
            content_hash=content_hash,
            scope=scope,
        )
        self.save(artifact)
        return artifact

    def save(self, artifact: Artifact) -> None:
        payload = (
            str(artifact.artifact_id),
            artifact.spec_version,
            artifact.artifact_type.value,
            artifact.producer,
            json.dumps([str(item) for item in artifact.parent_artifacts]),
            str(artifact.content_hash),
            artifact.scope.value,
        )
        cursor = self._connection.execute(
            "SELECT 1 FROM artifacts WHERE artifact_id = ?",
            (str(artifact.artifact_id),),
        )
        if cursor.fetchone() is not None:
            raise ValueError("Artifact IDs must be unique per run")
        self._connection.execute(
            """
            INSERT INTO artifacts (
                artifact_id,
                spec_version,
                artifact_type,
                producer,
                parent_artifacts,
                content_hash,
                scope
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        self._connection.commit()

    def load(self, artifact_id: ArtifactID) -> Artifact:
        cursor = self._connection.execute(
            """
            SELECT spec_version, artifact_type, producer, parent_artifacts,
                   content_hash, scope
            FROM artifacts WHERE artifact_id = ?
            """,
            (str(artifact_id),),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Artifact not found: {artifact_id}")
        parent_artifacts = tuple(ArtifactID(item) for item in json.loads(row[3]))
        return Artifact(
            spec_version=row[0],
            artifact_id=artifact_id,
            artifact_type=ArtifactType(row[1]),
            producer=row[2],
            parent_artifacts=parent_artifacts,
            content_hash=ContentHash(row[4]),
            scope=ArtifactScope(row[5]),
        )


class SqliteTraceStore:
    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path)
        SqliteMigrator(self._connection).migrate()

    def save_trace(self, trace: ExecutionTrace) -> None:
        payload = json.dumps(_encode_trace(trace))
        self._connection.execute(
            "REPLACE INTO traces (flow_id, trace_json) VALUES (?, ?)",
            (str(trace.flow_id), payload),
        )
        self._connection.commit()

    def load_trace(self, flow_id: FlowID) -> ExecutionTrace:
        cursor = self._connection.execute(
            "SELECT trace_json FROM traces WHERE flow_id = ?",
            (str(flow_id),),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Trace not found: {flow_id}")
        return _decode_trace(json.loads(row[0]))


class SqliteEntropyStore:
    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path)
        SqliteMigrator(self._connection).migrate()

    def save_usage(self, flow_id: FlowID, usage: tuple[EntropyUsage, ...]) -> None:
        rows = [
            (
                str(flow_id),
                index,
                entry.spec_version,
                entry.source.value,
                entry.magnitude.value,
                entry.description,
                entry.step_index,
            )
            for index, entry in enumerate(usage)
        ]
        self._connection.executemany(
            """
            INSERT OR REPLACE INTO entropy_usage (
                flow_id,
                entry_index,
                spec_version,
                source,
                magnitude,
                description,
                step_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self._connection.commit()

    def load_usage(self, flow_id: FlowID) -> tuple[EntropyUsage, ...]:
        cursor = self._connection.execute(
            """
            SELECT spec_version, source, magnitude, description, step_index
            FROM entropy_usage WHERE flow_id = ?
            ORDER BY entry_index
            """,
            (str(flow_id),),
        )
        return tuple(
            EntropyUsage(
                spec_version=row[0],
                source=EntropySource(row[1]),
                magnitude=EntropyMagnitude(row[2]),
                description=row[3],
                step_index=row[4],
            )
            for row in cursor.fetchall()
        )


def _encode_trace(trace: ExecutionTrace) -> dict[str, Any]:
    payload = asdict(trace)
    payload["flow_id"] = str(trace.flow_id)
    payload["parent_flow_id"] = (
        str(trace.parent_flow_id) if trace.parent_flow_id is not None else None
    )
    payload["child_flow_ids"] = [str(item) for item in trace.child_flow_ids]
    payload["determinism_level"] = trace.determinism_level.value
    payload["replay_acceptability"] = trace.replay_acceptability.value
    payload["dataset"] = _encode_dataset(trace.dataset)
    payload["replay_envelope"] = _encode_envelope(trace.replay_envelope)
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
    payload["contradiction_count"] = trace.contradiction_count
    payload["arbitration_decision"] = trace.arbitration_decision
    return payload


def _decode_trace(payload: dict[str, Any]) -> ExecutionTrace:
    return ExecutionTrace(
        spec_version=payload["spec_version"],
        flow_id=FlowID(payload["flow_id"]),
        parent_flow_id=FlowID(payload["parent_flow_id"])
        if payload["parent_flow_id"] is not None
        else None,
        child_flow_ids=tuple(FlowID(item) for item in payload["child_flow_ids"]),
        determinism_level=DeterminismLevel(payload["determinism_level"]),
        replay_acceptability=ReplayAcceptability(payload["replay_acceptability"]),
        dataset=_decode_dataset(payload["dataset"]),
        replay_envelope=_decode_envelope(payload["replay_envelope"]),
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
        contradiction_count=payload["contradiction_count"],
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


def _encode_dataset(dataset: DatasetDescriptor) -> dict[str, str]:
    return {
        "spec_version": dataset.spec_version,
        "dataset_id": str(dataset.dataset_id),
        "tenant_id": str(dataset.tenant_id),
        "dataset_version": dataset.dataset_version,
        "dataset_hash": dataset.dataset_hash,
        "dataset_state": dataset.dataset_state.value,
    }


def _decode_dataset(payload: dict[str, str]) -> DatasetDescriptor:
    return DatasetDescriptor(
        spec_version=payload["spec_version"],
        dataset_id=DatasetID(payload["dataset_id"]),
        tenant_id=TenantID(payload["tenant_id"]),
        dataset_version=payload["dataset_version"],
        dataset_hash=payload["dataset_hash"],
        dataset_state=DatasetState(payload["dataset_state"]),
    )
