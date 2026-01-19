# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import duckdb

from agentic_flows.runtime.context import RunMode
from agentic_flows.runtime.observability.execution_store_protocol import (
    ExecutionStoreProtocol,
)
from agentic_flows.spec.contracts.dataset_contract import (
    validate_dataset_descriptor,
    validate_transition,
)
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.model.dataset_descriptor import DatasetDescriptor
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.execution_event import ExecutionEvent
from agentic_flows.spec.model.execution_steps import ExecutionSteps
from agentic_flows.spec.model.execution_trace import ExecutionTrace
from agentic_flows.spec.model.replay_envelope import ReplayEnvelope
from agentic_flows.spec.model.retrieved_evidence import RetrievedEvidence
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
    RunID,
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
MIGRATIONS_DIR = Path(__file__).with_name("migrations")
SCHEMA_CONTRACT_PATH = Path(__file__).with_name("schema.sql")


class DuckDBExecutionStore(ExecutionStoreProtocol):
    def __init__(self, path: Path) -> None:
        self._connection = duckdb.connect(str(path))
        self._migrate()

    def save_run(
        self,
        *,
        trace: ExecutionTrace | None,
        plan: ExecutionSteps,
        mode: RunMode,
    ) -> RunID:
        run_id = RunID(str(uuid4()))
        created_at = datetime.now(tz=UTC).isoformat()
        finalized = bool(trace.finalized) if trace is not None else False
        trace_created = created_at
        if trace and trace.events:
            trace_created = trace.events[0].timestamp_utc
        self._connection.execute(
            """
            INSERT INTO runs (
                tenant_id,
                run_id,
                flow_id,
                flow_state,
                determinism_level,
                replay_acceptability,
                dataset_id,
                dataset_version,
                dataset_state,
                dataset_hash,
                dataset_storage_uri,
                allow_deprecated_datasets,
                replay_envelope_min_claim_overlap,
                replay_envelope_max_contradiction_delta,
                replay_envelope_require_same_arbitration,
                environment_fingerprint,
                plan_hash,
                verification_policy_fingerprint,
                resolver_id,
                parent_flow_id,
                contradiction_count,
                arbitration_decision,
                finalized,
                run_mode,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(plan.tenant_id),
                str(run_id),
                str(plan.flow_id),
                plan.flow_state.value,
                plan.determinism_level.value,
                plan.replay_acceptability.value,
                str(plan.dataset.dataset_id),
                plan.dataset.dataset_version,
                plan.dataset.dataset_state.value,
                plan.dataset.dataset_hash,
                plan.dataset.storage_uri,
                plan.allow_deprecated_datasets,
                plan.replay_envelope.min_claim_overlap,
                plan.replay_envelope.max_contradiction_delta,
                plan.replay_envelope.require_same_arbitration,
                str(plan.environment_fingerprint),
                str(plan.plan_hash),
                str(trace.verification_policy_fingerprint)
                if trace and trace.verification_policy_fingerprint is not None
                else None,
                str(trace.resolver_id) if trace else "unresolved",
                str(trace.parent_flow_id) if trace and trace.parent_flow_id else None,
                trace.contradiction_count if trace else 0,
                trace.arbitration_decision if trace else "none",
                finalized,
                mode.value,
                trace_created or created_at,
            ),
        )
        for child_flow_id in trace.child_flow_ids if trace else ():
            self._connection.execute(
                """
                INSERT INTO run_children (tenant_id, run_id, child_flow_id)
                VALUES (?, ?, ?)
                """,
                (str(plan.tenant_id), str(run_id), str(child_flow_id)),
            )
        for claim_id in trace.claim_ids if trace else ():
            self._connection.execute(
                """
                INSERT INTO claims (tenant_id, run_id, claim_id)
                VALUES (?, ?, ?)
                """,
                (str(plan.tenant_id), str(run_id), str(claim_id)),
            )
        self._connection.commit()
        return run_id

    def save_steps(
        self, *, run_id: RunID, tenant_id: TenantID, plan: ExecutionSteps
    ) -> None:
        for step in plan.steps:
            self._connection.execute(
                """
                INSERT INTO steps (
                    tenant_id,
                    run_id,
                    step_index,
                    agent_id,
                    step_type,
                    determinism_level,
                    inputs_fingerprint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(tenant_id),
                    str(run_id),
                    step.step_index,
                    str(step.agent_id),
                    step.step_type.value,
                    step.determinism_level.value,
                    str(step.inputs_fingerprint),
                ),
            )
            for dependency in step.declared_dependencies:
                self._connection.execute(
                    """
                    INSERT INTO step_dependencies (
                        tenant_id,
                        run_id,
                        step_index,
                        dependency_agent_id
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(tenant_id),
                        str(run_id),
                        step.step_index,
                        str(dependency),
                    ),
                )
        self._connection.commit()

    def save_events(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        events: tuple[ExecutionEvent, ...],
    ) -> None:
        for event in events:
            payload = event.payload or {}
            self._connection.execute(
                """
                INSERT INTO events (
                    tenant_id,
                    run_id,
                    event_index,
                    step_index,
                    event_type,
                    timestamp_utc,
                    payload_hash,
                    agent_id,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(tenant_id),
                    str(run_id),
                    event.event_index,
                    event.step_index,
                    event.event_type.value,
                    event.timestamp_utc,
                    str(event.payload_hash),
                    str(payload.get("agent_id")) if "agent_id" in payload else None,
                    json.dumps(payload, separators=(",", ":")),
                ),
            )
        self._connection.commit()

    def save_artifacts(self, *, run_id: RunID, artifacts: list[Artifact]) -> None:
        for artifact in artifacts:
            self._connection.execute(
                """
                INSERT INTO artifacts (
                    tenant_id,
                    run_id,
                    artifact_id,
                    artifact_type,
                    producer,
                    content_hash,
                    scope
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(artifact.tenant_id),
                    str(run_id),
                    str(artifact.artifact_id),
                    artifact.artifact_type.value,
                    artifact.producer,
                    str(artifact.content_hash),
                    artifact.scope.value,
                ),
            )
            for parent in artifact.parent_artifacts:
                self._connection.execute(
                    """
                    INSERT INTO artifact_parents (
                        tenant_id,
                        run_id,
                        artifact_id,
                        parent_artifact_id
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(artifact.tenant_id),
                        str(run_id),
                        str(artifact.artifact_id),
                        str(parent),
                    ),
                )
        self._connection.commit()

    def save_evidence(
        self, *, run_id: RunID, evidence: list[RetrievedEvidence]
    ) -> None:
        for index, item in enumerate(evidence):
            self._connection.execute(
                """
                INSERT INTO evidence (
                    tenant_id,
                    run_id,
                    entry_index,
                    evidence_id,
                    determinism,
                    source_uri,
                    content_hash,
                    score,
                    vector_contract_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.tenant_id),
                    str(run_id),
                    index,
                    str(item.evidence_id),
                    item.determinism.value,
                    item.source_uri,
                    str(item.content_hash),
                    item.score,
                    str(item.vector_contract_id),
                ),
            )
        self._connection.commit()

    def save_entropy_usage(
        self, *, run_id: RunID, usage: tuple[EntropyUsage, ...]
    ) -> None:
        for index, item in enumerate(usage):
            self._connection.execute(
                """
                INSERT INTO entropy_usage (
                    tenant_id,
                    run_id,
                    entry_index,
                    source,
                    magnitude,
                    description,
                    step_index
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.tenant_id),
                    str(run_id),
                    index,
                    item.source.value,
                    item.magnitude.value,
                    item.description,
                    item.step_index,
                ),
            )
        self._connection.commit()

    def save_tool_invocations(
        self,
        *,
        run_id: RunID,
        tenant_id: TenantID,
        tool_invocations: tuple[ToolInvocation, ...],
    ) -> None:
        for index, item in enumerate(tool_invocations):
            self._connection.execute(
                """
                INSERT INTO tool_invocations (
                    tenant_id,
                    run_id,
                    entry_index,
                    tool_id,
                    determinism_level,
                    inputs_fingerprint,
                    outputs_fingerprint,
                    duration,
                    outcome
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(tenant_id),
                    str(run_id),
                    index,
                    str(item.tool_id),
                    item.determinism_level.value,
                    str(item.inputs_fingerprint),
                    str(item.outputs_fingerprint)
                    if item.outputs_fingerprint is not None
                    else None,
                    item.duration,
                    item.outcome,
                ),
            )
        self._connection.commit()

    def register_dataset(self, dataset: DatasetDescriptor) -> None:
        validate_dataset_descriptor(dataset)
        self._assert_dvc_dataset(dataset)
        existing = self._connection.execute(
            """
            SELECT state FROM datasets
            WHERE tenant_id = ? AND dataset_id = ? AND version = ?
            """,
            (str(dataset.tenant_id), str(dataset.dataset_id), dataset.dataset_version),
        ).fetchone()
        previous = DatasetState(existing[0]) if existing else None
        validate_transition(previous, dataset.dataset_state)
        self._connection.execute(
            """
            INSERT OR REPLACE INTO datasets (
                tenant_id,
                dataset_id,
                version,
                state,
                previous_state,
                fingerprint,
                storage_uri
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(dataset.tenant_id),
                str(dataset.dataset_id),
                dataset.dataset_version,
                dataset.dataset_state.value,
                previous.value if previous is not None else None,
                dataset.dataset_hash,
                dataset.storage_uri,
            ),
        )
        self._connection.commit()

    def load_trace(self, run_id: RunID, *, tenant_id: TenantID) -> ExecutionTrace:
        run_row = self._connection.execute(
            """
            SELECT
                flow_id,
                flow_state,
                determinism_level,
                replay_acceptability,
                dataset_id,
                dataset_version,
                dataset_state,
                dataset_hash,
                dataset_storage_uri,
                allow_deprecated_datasets,
                replay_envelope_min_claim_overlap,
                replay_envelope_max_contradiction_delta,
                replay_envelope_require_same_arbitration,
                environment_fingerprint,
                plan_hash,
                verification_policy_fingerprint,
                resolver_id,
                parent_flow_id,
                contradiction_count,
                arbitration_decision,
                finalized
            FROM runs
            WHERE tenant_id = ? AND run_id = ?
            """,
            (str(tenant_id), str(run_id)),
        ).fetchone()
        if run_row is None:
            raise KeyError(f"Run not found: {run_id}")
        events = self._load_events(run_id, tenant_id=tenant_id)
        tool_invocations = self._load_tool_invocations(run_id, tenant_id=tenant_id)
        entropy_usage = self._load_entropy_usage(run_id, tenant_id=tenant_id)
        claim_ids = self._load_claim_ids(run_id, tenant_id=tenant_id)
        child_flow_ids = self._load_child_flow_ids(run_id, tenant_id=tenant_id)
        dataset = DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID(run_row[4]),
            tenant_id=tenant_id,
            dataset_version=run_row[5],
            dataset_hash=run_row[7],
            dataset_state=DatasetState(run_row[6]),
            storage_uri=run_row[8],
        )
        replay_envelope = ReplayEnvelope(
            spec_version="v1",
            min_claim_overlap=float(run_row[10]),
            max_contradiction_delta=int(run_row[11]),
            require_same_arbitration=bool(run_row[12]),
        )
        return ExecutionTrace(
            spec_version="v1",
            flow_id=FlowID(run_row[0]),
            tenant_id=tenant_id,
            parent_flow_id=FlowID(run_row[17]) if run_row[17] else None,
            child_flow_ids=child_flow_ids,
            flow_state=FlowState(run_row[1]),
            determinism_level=DeterminismLevel(run_row[2]),
            replay_acceptability=ReplayAcceptability(run_row[3]),
            dataset=dataset,
            replay_envelope=replay_envelope,
            allow_deprecated_datasets=bool(run_row[9]),
            environment_fingerprint=EnvironmentFingerprint(run_row[13]),
            plan_hash=PlanHash(run_row[14]),
            verification_policy_fingerprint=PolicyFingerprint(run_row[15])
            if run_row[15] is not None
            else None,
            resolver_id=ResolverID(run_row[16]),
            events=events,
            tool_invocations=tool_invocations,
            entropy_usage=entropy_usage,
            claim_ids=claim_ids,
            contradiction_count=int(run_row[18]),
            arbitration_decision=run_row[19],
            finalized=bool(run_row[20]),
        )

    def load_replay_envelope(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> ReplayEnvelope:
        row = self._connection.execute(
            """
            SELECT replay_envelope_min_claim_overlap,
                   replay_envelope_max_contradiction_delta,
                   replay_envelope_require_same_arbitration
            FROM runs
            WHERE tenant_id = ? AND run_id = ?
            """,
            (str(tenant_id), str(run_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        return ReplayEnvelope(
            spec_version="v1",
            min_claim_overlap=float(row[0]),
            max_contradiction_delta=int(row[1]),
            require_same_arbitration=bool(row[2]),
        )

    def load_dataset_descriptor(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> DatasetDescriptor:
        row = self._connection.execute(
            """
            SELECT dataset_id, dataset_version, dataset_state, dataset_hash, dataset_storage_uri
            FROM runs
            WHERE tenant_id = ? AND run_id = ?
            """,
            (str(tenant_id), str(run_id)),
        ).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        return DatasetDescriptor(
            spec_version="v1",
            dataset_id=DatasetID(row[0]),
            tenant_id=tenant_id,
            dataset_version=row[1],
            dataset_hash=row[3],
            dataset_state=DatasetState(row[2]),
            storage_uri=row[4],
        )

    def _load_events(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[ExecutionEvent, ...]:
        rows = self._connection.execute(
            """
            SELECT event_index, step_index, event_type, timestamp_utc, payload_hash, payload_json
            FROM events
            WHERE tenant_id = ? AND run_id = ?
            ORDER BY event_index
            """,
            (str(tenant_id), str(run_id)),
        ).fetchall()
        return tuple(
            ExecutionEvent(
                spec_version="v1",
                event_index=int(row[0]),
                step_index=int(row[1]),
                event_type=EventType(row[2]),
                timestamp_utc=row[3],
                payload=json.loads(row[5]) if row[5] else {},
                payload_hash=ContentHash(row[4]),
            )
            for row in rows
        )

    def _load_tool_invocations(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[ToolInvocation, ...]:
        rows = self._connection.execute(
            """
            SELECT tool_id, determinism_level, inputs_fingerprint, outputs_fingerprint, duration, outcome
            FROM tool_invocations
            WHERE tenant_id = ? AND run_id = ?
            """,
            (str(tenant_id), str(run_id)),
        ).fetchall()
        return tuple(
            ToolInvocation(
                spec_version="v1",
                tool_id=ToolID(row[0]),
                determinism_level=DeterminismLevel(row[1]),
                inputs_fingerprint=ContentHash(row[2]),
                outputs_fingerprint=ContentHash(row[3]) if row[3] else None,
                duration=float(row[4]),
                outcome=row[5],
            )
            for row in rows
        )

    def _load_entropy_usage(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[EntropyUsage, ...]:
        rows = self._connection.execute(
            """
            SELECT source, magnitude, description, step_index
            FROM entropy_usage
            WHERE tenant_id = ? AND run_id = ?
            ORDER BY entry_index
            """,
            (str(tenant_id), str(run_id)),
        ).fetchall()
        return tuple(
            EntropyUsage(
                spec_version="v1",
                tenant_id=tenant_id,
                source=EntropySource(row[0]),
                magnitude=EntropyMagnitude(row[1]),
                description=row[2],
                step_index=row[3],
            )
            for row in rows
        )

    def _load_claim_ids(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[ClaimID, ...]:
        rows = self._connection.execute(
            """
            SELECT claim_id FROM claims
            WHERE tenant_id = ? AND run_id = ?
            """,
            (str(tenant_id), str(run_id)),
        ).fetchall()
        return tuple(ClaimID(row[0]) for row in rows)

    def _load_child_flow_ids(
        self, run_id: RunID, *, tenant_id: TenantID
    ) -> tuple[FlowID, ...]:
        rows = self._connection.execute(
            """
            SELECT child_flow_id FROM run_children
            WHERE tenant_id = ? AND run_id = ?
            """,
            (str(tenant_id), str(run_id)),
        ).fetchall()
        return tuple(FlowID(row[0]) for row in rows)

    def _assert_dvc_dataset(self, dataset: DatasetDescriptor) -> None:
        if dataset.dataset_state is not DatasetState.FROZEN:
            return
        if dataset.storage_uri.startswith("file://"):
            path = Path(dataset.storage_uri.replace("file://", "", 1))
        else:
            path = Path(dataset.storage_uri)
        if not path.is_absolute() and not path.exists():
            for parent in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
                candidate = parent / path
                if candidate.exists():
                    path = candidate
                    break
        dvc_path = path.with_suffix(path.suffix + ".dvc")
        if not dvc_path.exists():
            raise ValueError(
                f"Frozen dataset requires DVC tracking: {dvc_path.as_posix()}"
            )

    def _migrate(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        migrations = self._load_migrations()
        applied = {
            int(row[0]): row[1]
            for row in self._connection.execute(
                "SELECT version, checksum FROM schema_migrations"
            ).fetchall()
        }
        latest_version = max(migrations.keys(), default=0)
        if applied and max(applied.keys()) > latest_version:
            raise RuntimeError(
                "Database schema is ahead of code migrations; refusing to start."
            )
        for version, statement in migrations.items():
            checksum = self._hash_payload(statement)
            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(
                        f"Migration checksum mismatch for version {version}"
                    )
                continue
            self._connection.execute("BEGIN")
            try:
                self._connection.execute(statement)
                self._connection.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum, applied_at)
                    VALUES (?, ?, ?)
                    """,
                    (version, checksum, datetime.now(tz=UTC).isoformat()),
                )
                self._connection.execute("COMMIT")
            except Exception:
                self._connection.execute("ROLLBACK")
                raise
        final_versions = {
            int(row[0])
            for row in self._connection.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }
        if final_versions != set(migrations.keys()):
            raise RuntimeError("Schema migrations are out of sync with code.")
        self._assert_schema_contract(latest_version)

    def _assert_schema_contract(self, latest_version: int) -> None:
        contract_payload = self._load_schema_contract()
        contract_hash = self._hash_payload(contract_payload)
        try:
            row = self._connection.execute(
                """
                SELECT schema_version, schema_hash
                FROM schema_contract
                ORDER BY schema_version DESC
                LIMIT 1
                """
            ).fetchone()
        except Exception as exc:
            raise RuntimeError(
                "Schema contract table missing; database schema is out of sync."
            ) from exc
        if row is None:
            self._connection.execute(
                """
                INSERT INTO schema_contract (schema_version, schema_hash, applied_at)
                VALUES (?, ?, ?)
                """,
                (latest_version, contract_hash, datetime.now(tz=UTC).isoformat()),
            )
            self._connection.commit()
            return
        stored_version, stored_hash = int(row[0]), row[1]
        if stored_version != latest_version:
            raise RuntimeError(
                "Database schema version does not match code contract version."
            )
        if stored_hash != contract_hash:
            raise RuntimeError("Database schema hash does not match code contract.")

    @staticmethod
    def _hash_payload(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _load_schema_contract() -> str:
        if not SCHEMA_CONTRACT_PATH.exists():
            raise RuntimeError("Schema contract file missing.")
        return SCHEMA_CONTRACT_PATH.read_text(encoding="utf-8")

    @staticmethod
    def _load_migrations() -> dict[int, str]:
        if not MIGRATIONS_DIR.exists():
            raise RuntimeError("Migration directory missing.")
        migrations: dict[int, str] = {}
        for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = int(file.name.split("_", 1)[0])
            migrations[version] = file.read_text(encoding="utf-8")
        return migrations


__all__ = ["DuckDBExecutionStore", "SCHEMA_CONTRACT_PATH", "SCHEMA_VERSION"]
