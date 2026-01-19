# Replay Breaks Contract

This document records changes that can or cannot break replay.
It is an internal invariant for engineers.

Allowed changes (do not break replay)
- Documentation edits only.
- New optional fields that default to existing explicit values in manifests and traces.
- Additional verification rules that are not enabled by default policy.
- New deterministic events that are excluded from semantic diff under invariant-preserving modes.

Breaking changes (must invalidate replay)
- Any change to plan hash inputs or execution ordering.
- Any change to dataset identity, dataset hash, or dataset state.
- Any change to determinism level or replay acceptability contract.
- Any change to artifact lineage rules or step contracts.
- Any change to verification policy fingerprints or arbitration rules.

Conditional breaks (policy-governed)
- Changes to statistical envelopes (claim overlap thresholds or contradiction deltas).
- Changes to allowable entropy sources or magnitude bounds.
- Changes to tolerated verification randomness.

Enforcement
- Compatibility tests must encode these rules.
- Replay validation must treat breaking changes as hard failures.
