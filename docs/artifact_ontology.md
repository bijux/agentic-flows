# Artifact Ontology

## Closed set of artifact types
- flow_manifest
- execution_plan
- resolved_step
- agent_invocation
- retrieval_request
- retrieved_evidence
- reasoning_step
- reasoning_claim
- reasoning_bundle
- verification_rule
- verification_result
- execution_event
- execution_trace

## Allowed dependencies
- flow_manifest: may depend on nothing.
- execution_plan: may depend on flow_manifest.
- resolved_step: may depend on flow_manifest, execution_plan.
- agent_invocation: may depend on resolved_step.
- retrieval_request: may depend on resolved_step.
- retrieved_evidence: may depend on retrieval_request.
- reasoning_step: may depend on resolved_step, retrieved_evidence, agent_invocation.
- reasoning_claim: may depend on reasoning_step, retrieved_evidence, agent_invocation.
- reasoning_bundle: may depend on reasoning_step, reasoning_claim.
- verification_rule: may depend on flow_manifest, resolved_step.
- verification_result: may depend on verification_rule, reasoning_bundle, retrieved_evidence, agent_invocation.
- execution_event: may depend on resolved_step, verification_result.
- execution_trace: may depend on execution_plan, execution_event.

## What cannot be an artifact
- Runtime state, caches, or in-memory objects.
- Environment variables, secrets, or credentials.
- Network responses without attribution.
- Undeclared side effects.
- Wall-clock time that is not tied to a declared artifact type.
