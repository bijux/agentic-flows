# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_FORBIDDEN_PREFIXES = (
    "agentic_flows.api",
    "agentic_flows.cli",
    "mkdocs",
    "tests",
    "pytest",
)


def test_runtime_does_not_import_forbidden_modules() -> None:
    runtime_root = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "agentic_flows"
        / "runtime"
    )
    offenders: list[str] = []

    for path in runtime_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                if any(
                    module == prefix or module.startswith(f"{prefix}.")
                    for prefix in _FORBIDDEN_PREFIXES
                ):
                    offenders.append(f"{path.relative_to(runtime_root)}:{module}")

    assert not offenders, f"runtime imports forbidden modules: {offenders}"


def _imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return [node.module] if node.module else []
    return []
