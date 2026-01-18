# Semantic Gaps

## Code that already matches semantics
- Stable input fingerprinting in `src/agentic_flows/runtime/fingerprint.py`.
- Stable timestamps in `src/agentic_flows/runtime/time.py`.
- Explicit execution plan and trace types in `src/agentic_flows/spec/execution_plan.py` and `src/agentic_flows/spec/execution_trace.py`.
- Determinism-focused tests in `tests/test_reasoning_determinism.py`, `tests/test_retrieval_determinism.py`, and `tests/test_replay_equivalence.py`.

## Code that violates semantics
- Artifact ontology is not enforced; `artifact_type` is unconstrained in `src/agentic_flows/spec/artifact.py`.
- Live execution emits an artifact type `reasoning` that is not in the closed ontology in `src/agentic_flows/runtime/live_executor.py`.
- Verification policy is hardcoded and not derived from flow semantics in `src/agentic_flows/runtime/live_executor.py`.

## Code that is premature
- Orchestration logic in `src/agentic_flows/runtime/live_executor.py` precedes finalized artifact ontology and determinism contract.
- Executor stubs in `src/agentic_flows/runtime/agent_executor.py`, `src/agentic_flows/runtime/retrieval_executor.py`, and `src/agentic_flows/runtime/reasoning_executor.py` precede bijux-* integration contracts.
- Verification engine scaffolding in `src/agentic_flows/runtime/verification_engine.py` precedes finalized verification semantics.
