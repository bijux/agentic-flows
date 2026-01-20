from agentic_flows.spec.model.execution.execution_trace import ExecutionTrace as NewTrace
from agentic_flows.spec.model.execution_trace import ExecutionTrace as OldTrace
from agentic_flows.spec.model.artifact.artifact import Artifact as NewArtifact
from agentic_flows.spec.model.artifact import Artifact as OldArtifact


def test_spec_model_import_stability() -> None:
    assert OldTrace is NewTrace
    assert OldArtifact is NewArtifact
