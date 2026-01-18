# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations


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


__all__ = [
    "ResolutionFailure",
    "ExecutionFailure",
    "RetrievalFailure",
    "ReasoningFailure",
    "VerificationFailure",
    "SemanticViolationError",
]
