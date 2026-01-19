# ARCHITECTURE

This document is internal and intentionally blunt.

Top-level packages

- core/: invariants, ids, and semantic rules. Must not import runtime, cli, or api.
- spec/: data models, contracts, ontology. Must not import runtime, cli, or api.
- runtime/: execution and orchestration only. Must not define semantics or policy.
- cli/: input/output adapter only. No validation or execution logic.
- api/: public surface only. No implementation logic.

Bad change example

Adding semantic validation inside `runtime/execution/*` or importing `agentic_flows.cli` from `runtime/*`.
