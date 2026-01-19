# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_flows.core.errors import (
    FAILURE_CLASS_MAP,
    FailureClass,
    SemanticViolationError,
    classify_failure,
)


def test_failure_taxonomy_is_exhaustive() -> None:
    expected = {
        "ResolutionFailure",
        "ExecutionFailure",
        "RetrievalFailure",
        "ReasoningFailure",
        "VerificationFailure",
        "SemanticViolationError",
    }
    assert {cls.__name__ for cls in FAILURE_CLASS_MAP} == expected


def test_failure_taxonomy_maps_semantic_violation() -> None:
    assert classify_failure(SemanticViolationError("boom")) == FailureClass.AUTHORITY


def test_failure_taxonomy_rejects_unknown() -> None:
    with pytest.raises(KeyError):
        classify_failure(RuntimeError("nope"))
