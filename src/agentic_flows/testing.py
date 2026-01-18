# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.runtime.fingerprint import fingerprint_inputs
from agentic_flows.spec.execution_plan import ExecutionPlan
from agentic_flows.spec.flow_manifest import FlowManifest
from agentic_flows.spec.ids import PlanHash
from agentic_flows.spec.resolved_flow import ResolvedFlow
from agentic_flows.spec.resolved_step import ResolvedStep
from agentic_flows.spec.verification import VerificationPolicy


def plan_hash_for(
    flow_id: str,
    steps: tuple[ResolvedStep, ...],
    dependencies: dict[str, list[str]],
) -> PlanHash:
    payload = {
        "flow_id": flow_id,
        "steps": [
            {
                "index": step.step_index,
                "agent_id": step.agent_id,
                "inputs_fingerprint": step.inputs_fingerprint,
                "declared_dependencies": list(step.declared_dependencies),
                "step_type": step.step_type,
            }
            for step in steps
        ],
        "dependencies": {
            agent_id: sorted(deps) for agent_id, deps in dependencies.items()
        },
    }
    return PlanHash(fingerprint_inputs(payload))


def resolved_flow_for(manifest: FlowManifest, plan: ExecutionPlan) -> ResolvedFlow:
    return ResolvedFlow(
        spec_version="v1",
        manifest=manifest,
        plan=plan,
    )


def baseline_policy() -> VerificationPolicy:
    return VerificationPolicy(
        spec_version="v1",
        verification_level="baseline",
        failure_mode="halt",
        required_evidence=(),
        rules=(),
        fail_on=(),
        escalate_on=(),
    )
