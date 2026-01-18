# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations


class ResolutionFailure(Exception):  # noqa: N818
    """Resolution failures as defined in docs/failures.md."""


class ExecutionFailure(Exception):  # noqa: N818
    """Execution failures as defined in docs/failures.md."""


class RetrievalFailure(Exception):  # noqa: N818
    """Retrieval failures as defined in docs/failures.md."""


class ReasoningFailure(Exception):  # noqa: N818
    """Reasoning failures as defined in docs/failures.md."""


class VerificationFailure(Exception):  # noqa: N818
    """Verification failures as defined in docs/failures.md."""


class SemanticViolationError(RuntimeError):
    """Runtime semantic invariant violation."""


__all__ = [
    "ResolutionFailure",
    "ExecutionFailure",
    "RetrievalFailure",
    "ReasoningFailure",
    "VerificationFailure",
    "SemanticViolationError",
]
