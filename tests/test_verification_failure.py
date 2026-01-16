import bijux_agent
import bijux_rar

from agentic_flows.runtime.live_executor import LiveExecutor
from agentic_flows.spec.agent_invocation import AgentInvocation
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.reasoning_bundle import ReasoningBundle
from agentic_flows.spec.reasoning_claim import ReasoningClaim
from agentic_flows.spec.reasoning_step import ReasoningStep
from agentic_flows.spec.resolved_step import ResolvedStep


def test_verification_failure_halts_flow() -> None:
    calls = {"agent": 0}

    def _run(**_kwargs):
        calls["agent"] += 1
        return [
            {
                "artifact_id": "agent-output",
                "artifact_type": "output",
                "content": "payload",
                "parent_artifacts": [],
            }
        ]

    bijux_agent.run = _run

    bijux_rar.reason = lambda **_kwargs: ReasoningBundle(
        bundle_id="bundle-1",
        claims=[
            ReasoningClaim(
                claim_id="claim-1",
                statement="statement",
                confidence=0.5,
                supported_by=[],
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
        evidence_ids=[],
        producer_agent_id="agent-a",
    )

    step_one = ResolvedStep(
        step_index=0,
        agent_id="agent-a",
        inputs_fingerprint="inputs-a",
        declared_dependencies=[],
        expected_artifacts=[],
        agent_invocation=AgentInvocation(
            agent_id="agent-a",
            agent_version="0.0.0",
            inputs_fingerprint="inputs-a",
            declared_outputs=[],
            execution_mode="deterministic",
        ),
        retrieval_request=None,
    )
    step_two = ResolvedStep(
        step_index=1,
        agent_id="agent-b",
        inputs_fingerprint="inputs-b",
        declared_dependencies=[],
        expected_artifacts=[],
        agent_invocation=AgentInvocation(
            agent_id="agent-b",
            agent_version="0.0.0",
            inputs_fingerprint="inputs-b",
            declared_outputs=[],
            execution_mode="deterministic",
        ),
        retrieval_request=None,
    )

    plan = ExecutionPlan(
        flow_id="flow-verify",
        steps=[step_one, step_two],
        environment_fingerprint="env",
        resolution_metadata=(("resolver_id", "agentic-flows:v0"),),
    )

    trace, _, _, _, _ = LiveExecutor().execute(plan)

    assert calls["agent"] == 1
    assert trace.events[-1].event_type == "VERIFICATION_FAIL"
