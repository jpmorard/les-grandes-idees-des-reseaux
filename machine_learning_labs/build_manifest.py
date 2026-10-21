"""Build and verify the SHA-256 manifest for the ML/RL laboratory package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifest.json"
MANAGED_PATHS = (
    "README.md",
    "SOURCES.md",
    "__init__.py",
    "build_environment_lock.py",
    "build_manifest.py",
    "dqn_relay_lab.py",
    "environment.lock.json",
    "notebooks/README.md",
    "notebooks/svd_radio.ipynb",
    "notebooks/tp_ml_classification_rare.ipynb",
    "notebooks/tp_rl_dqn_relais.ipynb",
    "notebooks/tp_rl_retour_q_td.ipynb",
    "pyproject.toml",
    "rare_classification_lab.py",
    "results/benchmark_results.json",
    "results/benchmark_summary.csv",
    "results/constrained_dqn_results.json",
    "results/constrained_dqn_summary.csv",
    "results/l25_robustness_results.json",
    "results/l25_robustness_summary.csv",
    "results/l26_abstention_results.json",
    "results/l26_abstention_summary.csv",
    "results/l27_support_guard_results.json",
    "results/l27_seed_contract_correction.json",
    "results/l27_support_guard_summary.csv",
    "return_td_lab.py",
    "run_benchmarks.py",
    "run_constrained_dqn_experiment.py",
    "run_l25_robustness_experiment.py",
    "run_l26_abstention_experiment.py",
    "run_l27_support_guard_experiment.py",
    "schemas/benchmark_results.schema.json",
    "schemas/constrained_dqn_results.schema.json",
    "schemas/l25_robustness_results.schema.json",
    "schemas/l26_abstention_results.schema.json",
    "schemas/l27_support_guard_results.schema.json",
    "tests/test_rl_labs.py",
    "uv.lock",
    "verify.py",
    "verify_notebooks.py",
)


def _role(path: str) -> str:
    if path.startswith("results/"):
        return "benchmark_evidence"
    if path.startswith("schemas/"):
        return "machine_readable_schema"
    if path.startswith("notebooks/"):
        return "executable_notebook"
    if path.endswith(".lock") or "lock." in path:
        return "environment_lock"
    if path.endswith(".md"):
        return "documentation"
    if path.endswith(".py"):
        return "executable_source"
    return "project_metadata"


def build_manifest() -> dict[str, object]:
    artifacts: list[dict[str, object]] = []
    for relative in MANAGED_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise AssertionError(f"missing managed artifact: {relative}")
        data = path.read_bytes()
        artifacts.append(
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "role": _role(relative),
            }
        )
    return {
        "schema_version": "1.0.0",
        "package_id": "network-book-machine-learning-labs-v1",
        "hash_algorithm": "sha256",
        "self_hash": None,
        "self_hash_note": "The manifest excludes itself to avoid recursion.",
        "artifacts": artifacts,
    }


def content() -> str:
    return json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n"


def write_or_check(*, check: bool) -> None:
    expected = content()
    if check:
        if (
            not MANIFEST_PATH.is_file()
            or MANIFEST_PATH.read_text(encoding="utf-8") != expected
        ):
            raise AssertionError("stale machine_learning_labs/manifest.json")
    else:
        MANIFEST_PATH.write_text(expected, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_or_check(check=args.check)
    print(MANIFEST_PATH)


if __name__ == "__main__":
    main()
