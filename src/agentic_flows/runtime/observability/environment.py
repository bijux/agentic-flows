# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# Fingerprinted: python version, OS platform, bijux package versions.
# Ignored: hostnames, environment variables.

from __future__ import annotations

from importlib import metadata
import platform
import sys

from agentic_flows.runtime.observability.fingerprint import fingerprint_inputs


def compute_environment_fingerprint() -> str:
    packages = {
        "bijux-agent": metadata.version("bijux-agent"),
        "bijux-cli": metadata.version("bijux-cli"),
        "bijux-rag": metadata.version("bijux-rag"),
        "bijux-rar": metadata.version("bijux-rar"),
        "bijux-vex": metadata.version("bijux-vex"),
    }
    snapshot = {
        "python_version": sys.version,
        "os": platform.platform(),
        "packages": packages,
    }
    return fingerprint_inputs(snapshot)
