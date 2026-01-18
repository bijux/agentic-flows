# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import pytest

from agentic_flows.spec.artifact_rules import validate_artifact_lineage
from agentic_flows.spec.ontology import ArtifactType


def test_artifact_lineage_violation_raises() -> None:
    with pytest.raises(ValueError, match="must not declare parent artifacts"):
        validate_artifact_lineage(
            parent_types=[ArtifactType.EXECUTION_TRACE],
            child_type=ArtifactType.FLOW_MANIFEST,
        )
