# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_spec_does_not_import_runtime() -> None:
    spec_root = Path(__file__).resolve().parents[3] / "src" / "agentic_flows" / "spec"
    offenders: list[str] = []

    for path in spec_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                if module == "agentic_flows.runtime" or module.startswith(
                    "agentic_flows.runtime."
                ):
                    offenders.append(f"{path.relative_to(spec_root)}:{module}")

    assert not offenders, f"spec imports runtime modules: {offenders}"


def _imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return [node.module] if node.module else []
    return []
