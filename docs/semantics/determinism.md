# Determinism Contract

This document elaborates on determinism; ../guarantees/system_guarantees.md defines guarantees.

## Inputs that define a run
- Flow manifest identifier and content.
- Declared determinism level and replay acceptability policy.
- Declared external inputs, including initial artifacts.
- Environment fingerprint.
- Resolver identity and resolution metadata.
- Agent configuration and version identifiers.
- Retrieval corpus identifiers and retrieval request parameters.

## Determinism levels
- STRICT: replay must be an exact match for all semantic outputs.
- BOUNDED: replay must preserve declared invariants and budgets.
- PROBABILISTIC: replay may vary within declared acceptability bounds.
- UNCONSTRAINED: replay is not required to match, but all entropy must be declared.

## Must be identical for replay
- For STRICT: the full set of inputs that define a run.
- For STRICT: step ordering and dependencies.
- For STRICT: artifact identities and contents.
- For STRICT: evidence set and ordering.
- For STRICT: verification rules and results.

## Allowed entropy
- Only entropy declared by determinism level and entropy budget.
- Non-semantic diagnostics may vary if explicitly marked and recorded.
- Undeclared randomness is a semantic violation.

## Not required to be identical
- Wall-clock duration.
- Resource usage metrics.
- Non-semantic log formatting.
