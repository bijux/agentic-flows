# INVARIANTS

Non-negotiables for agentic-flows.

- Runtime cannot define policy.
- Spec cannot execute.
- CLI cannot decide execution behavior.
- Determinism is mandatory for all runs.
- Execution must pass through execute_flow.
- Semantic violations are structural truth failures.
- Verification failures are epistemic truth failures.
- Traces must be finalized exactly once.
- Artifacts must flow through the artifact store.
- Public API is only what `api/__init__.py` exports.
