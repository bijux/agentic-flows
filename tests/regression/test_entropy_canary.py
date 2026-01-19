# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.observability.trace_diff import entropy_summary
from agentic_flows.spec.model.entropy_usage import EntropyUsage
from agentic_flows.spec.model.non_determinism_source import NonDeterminismSource
from agentic_flows.spec.ontology.ids import FlowID, TenantID
from agentic_flows.spec.ontology.ontology import EntropyMagnitude, EntropySource

pytestmark = pytest.mark.regression


def test_entropy_summary_reports_max_magnitude() -> None:
    usage = (
        EntropyUsage(
            spec_version="v1",
            tenant_id=TenantID("tenant-a"),
            source=EntropySource.SEEDED_RNG,
            magnitude=EntropyMagnitude.LOW,
            description="seeded",
            step_index=0,
            nondeterminism_source=NonDeterminismSource(
                source=EntropySource.SEEDED_RNG,
                authorized=True,
                scope=FlowID("flow-entropy"),
            ),
        ),
        EntropyUsage(
            spec_version="v1",
            tenant_id=TenantID("tenant-a"),
            source=EntropySource.DATA,
            magnitude=EntropyMagnitude.HIGH,
            description="data",
            step_index=1,
            nondeterminism_source=NonDeterminismSource(
                source=EntropySource.DATA,
                authorized=True,
                scope=FlowID("flow-entropy"),
            ),
        ),
    )

    summary = entropy_summary(usage)
    assert summary["sources"] == ["data", "seeded_rng"]
    assert summary["max_magnitude"] == EntropyMagnitude.HIGH.value
