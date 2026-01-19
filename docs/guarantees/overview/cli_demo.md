# CLI Demo Flow

Run the demo manifest in unsafe mode so failures are recorded and execution
continues:

```bash
agentic-flows unsafe-run docs/guarantees/overview/demo_flow.json
```

What to look for:

- A `STEP_FAILED` event for the `force-partial-failure` step.
- A `SEMANTIC_VIOLATION` event that records the failure explicitly.
- A later `STEP_END` event that shows recovery by continuing execution.
