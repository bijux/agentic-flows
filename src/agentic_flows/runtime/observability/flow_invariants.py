# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_flows.core.errors import SemanticViolationError
from agentic_flows.runtime.context import ExecutionContext
from agentic_flows.spec.model.artifact import Artifact
from agentic_flows.spec.ontology import ArtifactType


def validate_flow_invariants(
    context: ExecutionContext, artifacts: list[Artifact]
) -> None:
    _ensure_monotonic_artifact_growth(context)
    _ensure_artifact_provenance(artifacts)
    _ensure_no_orphan_artifacts(artifacts)


def _ensure_monotonic_artifact_growth(context: ExecutionContext) -> None:
    step_indices = sorted(context.recorded_steps())
    previous = 0
    for step_index in step_indices:
        current = len(context.artifacts_for_step(step_index))
        if current < previous:
            raise SemanticViolationError(
                "artifact growth must be monotonic across steps"
            )
        previous = current


def _ensure_artifact_provenance(artifacts: list[Artifact]) -> None:
    root_types = {
        ArtifactType.FLOW_MANIFEST,
        ArtifactType.EXECUTION_PLAN,
        ArtifactType.EXECUTION_TRACE,
        ArtifactType.EXECUTION_EVENT,
        ArtifactType.EXECUTOR_STATE,
        ArtifactType.AGENT_INVOCATION,
        ArtifactType.RETRIEVED_EVIDENCE,
    }
    for artifact in artifacts:
        if artifact.artifact_type in root_types:
            continue
        if len(artifact.parent_artifacts) == 0:
            raise SemanticViolationError("artifact provenance must include parents")


def _ensure_no_orphan_artifacts(artifacts: list[Artifact]) -> None:
    artifact_ids = {artifact.artifact_id for artifact in artifacts}
    for artifact in artifacts:
        for parent in artifact.parent_artifacts:
            if parent not in artifact_ids:
                raise SemanticViolationError("artifact parent must exist in flow")


__all__ = ["validate_flow_invariants"]
