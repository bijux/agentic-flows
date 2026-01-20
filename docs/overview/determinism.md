# Determinism
> Determinism boundaries for execution and replay guarantees.

## What determinism means here
Determinism means identical inputs, declared policies, and persisted contracts produce the same replay envelope and verification outcomes across runs.

## Sources of allowed nondeterminism
Allowed nondeterminism is restricted to explicitly authorized entropy sources that are budgeted, recorded, and reflected in the replay acceptability policy.

## What causes replay failure
Replay fails when contract fingerprints, dataset identity, environment fingerprints, or acceptability thresholds diverge from the recorded run.
