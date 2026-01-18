# bijux-* Contracts

## bijux-cli
- Must guarantee: passes declared inputs verbatim, records resolver identity, and surfaces failures without alteration.
- Must never do: mutate artifacts, invent evidence, suppress failures, or retry silently.
- Assumes true: agentic-flows provides validated manifests and stable resolution.

## bijux-agent
- Must guarantee: produces artifacts and reasoning tied to declared inputs and evidence.
- Must never do: use implicit memory, call undeclared tools, or emit hidden reasoning.
- Assumes true: step inputs, dependencies, and evidence are complete and authoritative.

## bijux-rag
- Must guarantee: retrieval results are attributable to a request and corpus identifier.
- Must never do: return best-effort results, reorder evidence without declaration, or retry silently.
- Assumes true: retrieval requests are fully specified and stable.

## bijux-rar
- Must guarantee: persists and returns artifacts exactly as recorded.
- Must never do: rewrite artifacts, delete artifacts, or alter identities.
- Assumes true: artifacts and evidence are immutable and correctly typed.

## bijux-vex
- Must guarantee: verification outcomes are reproducible from supplied inputs.
- Must never do: use opaque reasoning, accept unverifiable evidence, or pass without evidence.
- Assumes true: evidence and reasoning inputs are complete and attributable.
