# Spec Law

This document defines what the specification layer is allowed to do and what it must never do.

## Allowed
- Define immutable data models with no policy or side effects.
- Define ontology symbols and identifiers used across the system.
- Define validation contracts that raise on semantic violations.

## Forbidden
- No runtime imports or behavior.
- No I/O, environment inspection, or side effects.
- No implicit defaults that change behavior.
- No validation inside model constructors.

## Review Rules
- Model changes require contract updates or explicit justification.
- Contract changes must cite the relevant semantics document.
- Ontology changes must update all call sites or tests must fail.
