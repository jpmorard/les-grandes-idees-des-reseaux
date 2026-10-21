"""Record the exact environment that produced the retained ML/RL evidence."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / "environment.lock.json"
PACKAGES = ("gymnasium", "jupyter", "matplotlib", "numpy", "pandas", "torch")


def snapshot() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "evidence_environment": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "project_contract": {
            "python": ">=3.12,<3.15",
            "device": "cpu",
            "network_required": False,
            "privileges_required": False,
            "dependency_lock": "uv.lock",
        },
        "packages": {
            name: importlib.metadata.version(name) for name in PACKAGES
        },
        "python_executable_name": Path(sys.executable).name,
    }


def content() -> str:
    return json.dumps(snapshot(), indent=2, sort_keys=True) + "\n"


def write_or_check(*, check: bool) -> None:
    expected = content()
    if check:
        if not LOCK_PATH.is_file() or LOCK_PATH.read_text(encoding="utf-8") != expected:
            raise AssertionError(
                "environment differs from the retained evidence producer; "
                "use the lock or regenerate the evidence intentionally"
            )
    else:
        LOCK_PATH.write_text(expected, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_or_check(check=args.check)
    print(LOCK_PATH)


if __name__ == "__main__":
    main()
