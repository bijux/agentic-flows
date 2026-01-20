# Storage Model
> How persistence and dataset governance work together.

DuckDB is used as the canonical store because it provides durable, queryable, and audited execution records in one place. It enables strict schema enforcement and replay comparisons without ad-hoc serialization. This keeps execution history consistent across runs and environments.

DVC controls dataset identity, versioning, and immutability boundaries for replayable data. It is the single authority for dataset fingerprints and frozen artifacts. DuckDB records those identities but does not replace DVC as the dataset system of record.

Bypassing DVC breaks dataset provenance, invalidates replay guarantees, and makes stored runs unverifiable. It also severs the link between persisted runs and the dataset contract. The system treats such runs as invalid for replay acceptance.
