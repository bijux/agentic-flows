# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

import agentic_flows

from agentic_flows.runtime.resolver import FlowResolver
from agentic_flows.spec.flow_manifest import FlowManifest


def test_imports() -> None:
    resolver = FlowResolver()
    _ = resolver.resolver_id
    assert FlowResolver
    assert FlowManifest
    assert set(agentic_flows.__all__) == {"FlowManifest", "FlowResolver"}
