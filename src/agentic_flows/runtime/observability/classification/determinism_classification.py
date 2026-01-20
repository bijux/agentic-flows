# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for runtime/observability/classification/determinism_classification.py."""

from __future__ import annotations

from enum import Enum

from agentic_flows.spec.model.execution.execution_trace import ExecutionTrace
from agentic_flows.spec.ontology import DeterminismLevel
from agentic_flows.spec.ontology.public import (
    DeterminismClass,
    EntropySource,
    EventType,
)


class EntropySeverity(str, Enum):
    """Entropy severity; misuse breaks entropy classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


EVENT_DETERMINISM_CLASS: dict[EventType, DeterminismClass] = {
    EventType.STEP_START: DeterminismClass.STRUCTURAL,
    EventType.STEP_END: DeterminismClass.STRUCTURAL,
    EventType.STEP_FAILED: DeterminismClass.STRUCTURAL,
    EventType.RETRIEVAL_START: DeterminismClass.STRUCTURAL,
    EventType.RETRIEVAL_END: DeterminismClass.STRUCTURAL,
    EventType.RETRIEVAL_FAILED: DeterminismClass.STRUCTURAL,
    EventType.REASONING_START: DeterminismClass.STRUCTURAL,
    EventType.REASONING_END: DeterminismClass.STRUCTURAL,
    EventType.REASONING_FAILED: DeterminismClass.STRUCTURAL,
    EventType.VERIFICATION_START: DeterminismClass.STRUCTURAL,
    EventType.VERIFICATION_PASS: DeterminismClass.STRUCTURAL,
    EventType.VERIFICATION_FAIL: DeterminismClass.STRUCTURAL,
    EventType.VERIFICATION_ESCALATE: DeterminismClass.STRUCTURAL,
    EventType.VERIFICATION_ARBITRATION: DeterminismClass.STRUCTURAL,
    EventType.EXECUTION_INTERRUPTED: DeterminismClass.STRUCTURAL,
    EventType.SEMANTIC_VIOLATION: DeterminismClass.STRUCTURAL,
    EventType.TOOL_CALL_START: DeterminismClass.EXTERNAL,
    EventType.TOOL_CALL_END: DeterminismClass.EXTERNAL,
    EventType.TOOL_CALL_FAIL: DeterminismClass.EXTERNAL,
    EventType.HUMAN_INTERVENTION: DeterminismClass.HUMAN,
}

ENTROPY_SOURCE_SEVERITY: dict[EntropySource, EntropySeverity] = {
    EntropySource.SEEDED_RNG: EntropySeverity.LOW,
    EntropySource.DATA: EntropySeverity.MEDIUM,
    EntropySource.EXTERNAL_ORACLE: EntropySeverity.HIGH,
    EntropySource.HUMAN_INPUT: EntropySeverity.CRITICAL,
}

ENTROPY_SOURCE_CLASS: dict[EntropySource, DeterminismClass] = {
    EntropySource.SEEDED_RNG: DeterminismClass.STOCHASTIC,
    EntropySource.DATA: DeterminismClass.STOCHASTIC,
    EntropySource.EXTERNAL_ORACLE: DeterminismClass.EXTERNAL,
    EntropySource.HUMAN_INPUT: DeterminismClass.HUMAN,
}


def determinism_class_for_event(event_type: EventType) -> DeterminismClass:
    """Classify determinism for an event; misuse breaks reporting."""
    return EVENT_DETERMINISM_CLASS[event_type]


def entropy_source_severity(source: EntropySource) -> EntropySeverity:
    """Map entropy source to severity; misuse breaks audit severity."""
    return ENTROPY_SOURCE_SEVERITY[source]


def determinism_class_for_entropy_source(source: EntropySource) -> DeterminismClass:
    """Classify determinism for entropy source; misuse breaks reporting."""
    return ENTROPY_SOURCE_CLASS[source]


def determinism_classes_for_trace(trace: ExecutionTrace) -> list[str]:
    """Summarize determinism classes; misuse breaks drift detection."""
    classes: set[DeterminismClass] = set()
    if trace.events:
        classes.add(DeterminismClass.STRUCTURAL)
    if trace.environment_fingerprint:
        classes.add(DeterminismClass.ENVIRONMENTAL)
    if trace.determinism_level in {
        DeterminismLevel.PROBABILISTIC,
        DeterminismLevel.UNCONSTRAINED,
    }:
        classes.add(DeterminismClass.STOCHASTIC)
    for event in trace.events:
        classes.add(determinism_class_for_event(event.event_type))
    if trace.tool_invocations:
        classes.add(DeterminismClass.EXTERNAL)
    for entry in trace.entropy_usage:
        classes.add(determinism_class_for_entropy_source(entry.source))
    return sorted(item.value for item in classes)


__all__ = [
    "EntropySeverity",
    "determinism_class_for_event",
    "determinism_class_for_entropy_source",
    "determinism_classes_for_trace",
    "entropy_source_severity",
]
