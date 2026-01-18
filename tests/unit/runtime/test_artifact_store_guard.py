# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.artifact_store import InMemoryArtifactStore
from agentic_flows.spec.ontology.ids import ArtifactID, ContentHash
from agentic_flows.spec.ontology.ontology import ArtifactType

pytestmark = pytest.mark.unit


def test_artifact_store_creates_and_saves_artifact() -> None:
    store = InMemoryArtifactStore()
    artifact = store.create(
        spec_version="v1",
        artifact_id=ArtifactID("artifact-1"),
        artifact_type=ArtifactType.AGENT_INVOCATION,
        producer="agent",
        parent_artifacts=(),
        content_hash=ContentHash("hash"),
    )

    loaded = store.load(artifact.artifact_id)
    assert loaded == artifact
