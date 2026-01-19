# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.runtime.observability.entropy import EntropyLedger
from agentic_flows.spec.model.entropy_budget import EntropyBudget
from agentic_flows.spec.model.non_determinism_source import NonDeterminismSource
from agentic_flows.spec.ontology.ids import FlowID, TenantID
from agentic_flows.spec.ontology.ontology import EntropyMagnitude, EntropySource


@pytest.mark.unit
@pytest.mark.xfail(reason="entropy authorization is not enforced yet")
def test_unauthorized_entropy_intent() -> None:
    ledger = EntropyLedger(
        EntropyBudget(
            spec_version="v1",
            allowed_sources=(EntropySource.EXTERNAL_ORACLE,),
            max_magnitude=EntropyMagnitude.LOW,
        )
    )
    with pytest.raises(ValueError):
        ledger.record(
            tenant_id=TenantID("tenant-a"),
            source=EntropySource.EXTERNAL_ORACLE,
            magnitude=EntropyMagnitude.LOW,
            description="unauthorized entropy",
            step_index=0,
            nondeterminism_source=NonDeterminismSource(
                source=EntropySource.EXTERNAL_ORACLE,
                authorized=False,
                scope=FlowID("flow-entropy"),
            ),
        )
