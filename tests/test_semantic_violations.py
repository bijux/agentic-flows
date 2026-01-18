# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.spec.artifact_rules import validate_artifact_lineage
from agentic_flows.spec.artifact_types import ArtifactType


def test_artifact_lineage_violation_raises() -> None:
    with pytest.raises(ValueError):
        validate_artifact_lineage(
            parent_types=[ArtifactType.EXECUTION_TRACE],
            child_type=ArtifactType.FLOW_MANIFEST,
        )
