import platform
import sys
from importlib import metadata

from agentic_flows.runtime.fingerprint import fingerprint_inputs


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
