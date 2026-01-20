Semantic versioning rules apply to all public CLI and API contracts.
PATCH increments cover documentation fixes and non-functional changes.
Example PATCH: correcting a typo in API field descriptions.
MINOR increments cover additive, backward-compatible API fields and new CLI flags.
Example MINOR: adding an optional header or response field without changing meaning.
MAJOR increments cover any change that can alter replay equivalence or public contracts.
Example MAJOR: changing determinism classification semantics or required headers.
