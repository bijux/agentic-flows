# Determinism Contract

## Inputs that define a run
- Flow manifest identifier and content.
- Declared external inputs, including initial artifacts.
- Environment fingerprint.
- Resolver identity and resolution metadata.
- Agent configuration and version identifiers.
- Retrieval corpus identifiers and retrieval request parameters.

## Must be identical for replay
- The full set of inputs that define a run.
- Step ordering and dependencies.
- Artifact identities and contents.
- Evidence set and ordering.
- Verification rules and results.

## Allowed entropy
- None for semantic outputs.
- Non-semantic diagnostics may vary if explicitly marked as such.

## Not required to be identical
- Wall-clock duration.
- Resource usage metrics.
- Non-semantic log formatting.
