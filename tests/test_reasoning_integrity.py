import bijux_agent
import bijux_rar

from agentic_flows.runtime.live_executor import LiveExecutor
from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep
from agentic_flows.spec.resolved_step import ResolvedStep


def test_reasoning_references_missing_evidence() -> None:
    bijux_agent.run = lambda **_kwargs: [
        {
            "artifact_id": "agent-output",
            "artifact_type": "output",
            "content": "payload",
            "parent_artifacts": [],
        }
    ]

    def _bad_reason(**_kwargs):
        return ReasoningBundle(
            bundle_id="bundle-1",
            claims=[
                ReasoningClaim(
                    claim_id="claim-1",
                    statement="statement",
                    confidence=0.5,
                    supported_by=["missing-evidence"],
                )
            ],
            steps=[
                ReasoningStep(
                    step_id="step-1",
                    input_claims=[],
                    output_claims=["claim-1"],
                    method="deduction",
                )
            ],
            evidence_ids=["missing-evidence"],
            producer_agent_id="agent-a",
        )

    bijux_rar.reason = _bad_reason

    step = ResolvedStep(
        step_index=0,
        agent_id="agent-a",
        inputs_fingerprint="inputs",
        declared_dependencies=[],
        expected_artifacts=[],
        agent_invocation=AgentInvocation(
            agent_id="agent-a",
            agent_version="0.0.0",
            inputs_fingerprint="inputs",
            declared_outputs=[],
            execution_mode="deterministic",
        ),
        retrieval_request=None,
    )
    plan = ExecutionPlan(
        flow_id="flow-reasoning",
        steps=[step],
        environment_fingerprint="env",
        resolution_metadata=(("resolver_id", "agentic-flows:v0"),),
    )

    trace, artifacts, evidence, _, _ = LiveExecutor().execute(plan)

    assert evidence == []
    assert trace.events[-1].event_type == "REASONING_FAILED"
