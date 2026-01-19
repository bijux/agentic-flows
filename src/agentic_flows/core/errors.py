# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from enum import Enum


class ResolutionFailure(Exception):  # noqa: N818
    """Resolution failures (structural truth) as defined in docs/failures.md."""


class ExecutionFailure(Exception):  # noqa: N818
    """Execution failures (structural truth) as defined in docs/failures.md."""


class RetrievalFailure(Exception):  # noqa: N818
    """Retrieval failures (structural truth) as defined in docs/failures.md."""


class ReasoningFailure(Exception):  # noqa: N818
    """Reasoning failures (structural truth) as defined in docs/failures.md."""


class VerificationFailure(Exception):  # noqa: N818
    """Verification failures (epistemic truth) as defined in docs/failures.md."""


class SemanticViolationError(RuntimeError):
    """Semantic violations (structural truth) enforced by authority."""


class FailureClass(str, Enum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    ENVIRONMENTAL = "environmental"
    AUTHORITY = "authority"


FAILURE_CLASS_MAP = {
    ResolutionFailure: FailureClass.STRUCTURAL,
    ExecutionFailure: FailureClass.STRUCTURAL,
    RetrievalFailure: FailureClass.STRUCTURAL,
    ReasoningFailure: FailureClass.STRUCTURAL,
    VerificationFailure: FailureClass.SEMANTIC,
    SemanticViolationError: FailureClass.AUTHORITY,
}


def classify_failure(exc: BaseException) -> FailureClass:
    for failure_type, failure_class in FAILURE_CLASS_MAP.items():
        if isinstance(exc, failure_type):
            return failure_class
    raise KeyError(f"Unclassified failure: {type(exc).__name__}")


__all__ = [
    "ResolutionFailure",
    "ExecutionFailure",
    "RetrievalFailure",
    "ReasoningFailure",
    "VerificationFailure",
    "SemanticViolationError",
    "FailureClass",
    "FAILURE_CLASS_MAP",
    "classify_failure",
]
