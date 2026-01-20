from agentic_flows.runtime.observability.execution_store import DuckDBExecutionStore
from agentic_flows.runtime.observability.trace_diff import semantic_trace_diff
from agentic_flows.runtime.observability.trace_recorder import TraceRecorder
from agentic_flows.runtime.observability.determinism_classification import (
    determinism_classes_for_trace,
)


def test_observability_legacy_imports():
    assert DuckDBExecutionStore is not None
    assert semantic_trace_diff is not None
    assert TraceRecorder is not None
    assert determinism_classes_for_trace is not None
