# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import pytest

from agentic_flows.spec.execution_trace import ExecutionTrace
from agentic_flows.spec.ids import EnvironmentFingerprint, FlowID, ResolverID


def test_trace_access_before_finalize_raises() -> None:
    trace = ExecutionTrace(
        spec_version="v1",
        flow_id=FlowID("flow-misuse"),
        environment_fingerprint=EnvironmentFingerprint("env"),
        resolver_id=ResolverID("agentic-flows:v0"),
        events=(),
        finalized=False,
    )

    with pytest.raises(RuntimeError, match="ExecutionTrace accessed before finalization"):
        _ = trace.flow_id
