# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

# Non-Determinism Design Contract

- Allowed randomness is explicitly declared via entropy sources and bounded by the
  flow's entropy budget.
- Data-derived entropy (sampling, ranking variance, truncation) must be recorded
  with EntropySource.DATA and an explicit magnitude.
- Randomness from system time, ambient process state, or hidden library calls is
  forbidden.
- Any entropy usage without a declared budget is a semantic violation and must
  abort the run.
- Replay evaluation must use the flow's replay envelope and determinism level
  rather than assuming equality.
- Dataset identity is part of replay truth; mismatched dataset hashes are replay
  failures unless an explicit policy allows drift.
