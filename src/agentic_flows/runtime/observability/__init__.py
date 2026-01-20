# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib
import sys
import types

__all__ = []


def _alias_module(old: str, new: str) -> None:
    module = types.ModuleType(old)
    attr_name = old.rsplit(".", 1)[-1]

    def _load_target():
        target = importlib.import_module(new)
        sys.modules[old] = target
        setattr(sys.modules[__name__], attr_name, target)
        return target

    def _module_getattr(name: str) -> object:
        target = _load_target()
        return getattr(target, name)

    def _module_dir() -> list[str]:
        target = _load_target()
        return list(dir(target))

    def _module_setattr(name: str, value: object) -> None:
        target = _load_target()
        setattr(target, name, value)

    module.__getattr__ = _module_getattr  # type: ignore[attr-defined]
    module.__dir__ = _module_dir  # type: ignore[attr-defined]
    module.__setattr__ = _module_setattr  # type: ignore[attr-defined]
    sys.modules[old] = module
    setattr(sys.modules[__name__], attr_name, module)


_alias_module(
    "agentic_flows.runtime.observability.trace_recorder",
    "agentic_flows.runtime.observability.capture.trace_recorder",
)
_alias_module(
    "agentic_flows.runtime.observability.observed_run",
    "agentic_flows.runtime.observability.capture.observed_run",
)
_alias_module(
    "agentic_flows.runtime.observability.hooks",
    "agentic_flows.runtime.observability.capture.hooks",
)
_alias_module(
    "agentic_flows.runtime.observability.time",
    "agentic_flows.runtime.observability.capture.time",
)
_alias_module(
    "agentic_flows.runtime.observability.environment",
    "agentic_flows.runtime.observability.capture.environment",
)
_alias_module(
    "agentic_flows.runtime.observability.execution_store",
    "agentic_flows.runtime.observability.storage.execution_store",
)
_alias_module(
    "agentic_flows.runtime.observability.execution_store_protocol",
    "agentic_flows.runtime.observability.storage.execution_store_protocol",
)
_alias_module(
    "agentic_flows.runtime.observability.schema_contracts",
    "agentic_flows.runtime.observability.storage.schema_contracts",
)
_alias_module(
    "agentic_flows.runtime.observability.trace_diff",
    "agentic_flows.runtime.observability.analysis.trace_diff",
)
_alias_module(
    "agentic_flows.runtime.observability.comparative_analysis",
    "agentic_flows.runtime.observability.analysis.comparative_analysis",
)
_alias_module(
    "agentic_flows.runtime.observability.drift",
    "agentic_flows.runtime.observability.analysis.drift",
)
_alias_module(
    "agentic_flows.runtime.observability.flow_invariants",
    "agentic_flows.runtime.observability.analysis.flow_invariants",
)
_alias_module(
    "agentic_flows.runtime.observability.flow_correlation",
    "agentic_flows.runtime.observability.analysis.flow_correlation",
)
_alias_module(
    "agentic_flows.runtime.observability.determinism_classification",
    "agentic_flows.runtime.observability.classification.determinism_classification",
)
_alias_module(
    "agentic_flows.runtime.observability.entropy",
    "agentic_flows.runtime.observability.classification.entropy",
)
_alias_module(
    "agentic_flows.runtime.observability.fingerprint",
    "agentic_flows.runtime.observability.classification.fingerprint",
)
_alias_module(
    "agentic_flows.runtime.observability.seed",
    "agentic_flows.runtime.observability.classification.seed",
)
_alias_module(
    "agentic_flows.runtime.observability.retrieval_fingerprint",
    "agentic_flows.runtime.observability.classification.retrieval_fingerprint",
)
