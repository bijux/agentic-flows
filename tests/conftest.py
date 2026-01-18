# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
from __future__ import annotations

import sys
import types


def pytest_configure() -> None:
    if "bijux_cli" not in sys.modules:
        stub = types.ModuleType("bijux_cli")
        stub.__version__ = "0.0.0"
        sys.modules["bijux_cli"] = stub
    if "bijux_agent" not in sys.modules:
        stub = types.ModuleType("bijux_agent")
        stub.__version__ = "0.0.0"
        stub.run = lambda **_kwargs: []
        sys.modules["bijux_agent"] = stub
    if "bijux_rag" not in sys.modules:
        stub = types.ModuleType("bijux_rag")
        stub.retrieve = lambda **_kwargs: []
        sys.modules["bijux_rag"] = stub
    if "bijux_vex" not in sys.modules:
        stub = types.ModuleType("bijux_vex")
        stub.enforce_contract = lambda *_args, **_kwargs: True
        sys.modules["bijux_vex"] = stub
    if "bijux_rar" not in sys.modules:
        stub = types.ModuleType("bijux_rar")
        stub.reason = lambda **_kwargs: None
        sys.modules["bijux_rar"] = stub
