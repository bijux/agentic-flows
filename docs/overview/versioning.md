# Versioning
> Rules for changes in the first public release.

This is the first public release and the rules start here.
MAJOR: any change that can alter replay equivalence, persisted schema, or public contracts.
MINOR: additive, backward-compatible changes to public CLI, HTTP schema, or ontology values.
PATCH: documentation fixes, refactors, or internal changes with identical behavior.
Example PATCH: comment fixes or file moves with no API impact.
Example MINOR: adding an optional response field or a new CLI flag that preserves defaults.
Example MAJOR: changing determinism semantics, replay rules, or required fields.
