# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agentic_flows.cli.main import _load_manifest, _load_policy
from agentic_flows.runtime.observability.storage.execution_store import (
    DuckDBExecutionWriteStore,
)
from agentic_flows.runtime.orchestration.execute_flow import (
    ExecutionConfig,
    RunMode,
    execute_flow,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "examples" / "boring" / "flow.json"
    policy_path = root / "examples" / "boring" / "policy.json"
    db_path = Path("/tmp/agentic_flows_minimal.duckdb")

    manifest = _load_manifest(manifest_path)
    policy = _load_policy(policy_path)

    store = DuckDBExecutionWriteStore(db_path)
    config = ExecutionConfig(
        mode=RunMode.LIVE,
        determinism_level=manifest.determinism_level,
        verification_policy=policy,
        execution_store=store,
    )
    result = execute_flow(manifest=manifest, config=config)
    if result.run_id is None:
        raise RuntimeError("run_id missing from execution result")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_flows.cli.main",
            "replay",
            str(manifest_path),
            "--policy",
            str(policy_path),
            "--run-id",
            str(result.run_id),
            "--tenant-id",
            str(manifest.tenant_id),
            "--db-path",
            str(db_path),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
