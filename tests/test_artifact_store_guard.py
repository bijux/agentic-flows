# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import pytest

from agentic_flows.spec.artifact import Artifact
from agentic_flows.spec.ids import ArtifactID, ContentHash
from agentic_flows.spec.ontology import ArtifactType


def test_artifact_creation_requires_store() -> None:
    with pytest.raises(
        RuntimeError, match="Artifacts must be created via ArtifactStore"
    ):
        Artifact(
            spec_version="v1",
            artifact_id=ArtifactID("artifact-1"),
            artifact_type=ArtifactType.AGENT_INVOCATION,
            producer="agent",
            parent_artifacts=(),
            content_hash=ContentHash("hash"),
        )
