# Versioning Rules

This project follows semantic versioning with explicit rules for replay and determinism.

## Breaking Replay (major)
- Changes to trace schema, replay envelope, or execution plan hashing.
- Changes to dataset identity or dataset hash semantics.
- Any modification that makes previously stored runs unreplayable or unverifiable.

## Breaking Determinism (major)
- New entropy sources or changes to entropy accounting.
- Changes to determinism classification or replay acceptability semantics.
- Any change that alters deterministic ordering guarantees.

## Allowed Evolution (minor)
- Additive fields with defaults that preserve existing traces.
- New CLI commands or APIs that do not alter existing behavior.
- New verification rules that are opt-in.

## Fixes (patch)
- Bug fixes that preserve replay results and determinism guarantees.
- Documentation and tooling updates with no behavior change.
