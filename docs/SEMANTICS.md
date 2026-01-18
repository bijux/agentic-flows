# SEMANTICS

This document defines system guarantees. If any other document conflicts, this one wins.

## Agentic Flow
- A named specification of steps and their dependencies.
- Declares required inputs and expected outputs.
- Defines verification requirements for the flow outcome.
- Has a single authoritative version per run.
- Must be resolvable into an ordered set of steps.

## Step
- Minimal unit of execution within a flow.
- Declares its inputs, outputs, and dependencies.
- Produces zero or more artifacts.
- Has explicit verification requirements.
- Executes at most once per run.

## Artifact
- Immutable record produced by a step or derivation.
- Has a stable identity and a declared type.
- References its producer and parent artifacts.
- May be used as input to later steps.
- Must be preservable for replay and verification.

## Evidence
- Record used to support verification decisions.
- Must be attributable to a specific source or artifact.
- Must be sufficient to justify a verification result.
- Must be preserved or referenced.

## Reasoning
- Explicit linkage between evidence and claims.
- Must be auditable and attributable.
- Must reference the evidence it depends on.
- Must not include hidden or implicit content.
- May be empty if no claims are made.

## Verification
- Determination of whether requirements are met.
- Consumes artifacts, evidence, and reasoning.
- Produces a definitive status and basis.
- Must be reproducible for the same inputs.
