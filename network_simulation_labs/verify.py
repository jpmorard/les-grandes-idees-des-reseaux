"""Verify contracts, reproducibility, security boundaries, and artifact hashes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import (
    ContractError,
    load_json,
    validate_calibration_trace,
    validate_emulation_request,
    validate_routing_replay,
    validate_scenario,
)
from .notebook_contracts import verify_notebooks
from .run_labs import DATASETS, PLAN_PATH, RESULT_PATH, ROOT, build_artifacts, canonical_json


MANIFEST_PATH = ROOT / "manifest.json"
IGNORED_NAMES = {"manifest.json", ".DS_Store"}
IGNORED_PARTS = {"__pycache__"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.name in IGNORED_NAMES:
            continue
        if path.is_symlink():
            raise ContractError(f"symlink forbidden: {relative}")
        if ".lock" in path.name:
            raise ContractError(f"lock-named artifact forbidden: {relative}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def build_manifest() -> dict[str, Any]:
    return {
        "manifest_version": "1.0",
        "algorithm": "sha256",
        "scope": "all files below network_simulation_labs except manifest.json and runtime caches",
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in artifact_files()
        ],
    }


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot parse {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def _verify_python_boundary() -> None:
    forbidden_modules = {"subprocess", "pty"}
    forbidden_calls = {"system", "popen", "spawnl", "spawnlp", "spawnv", "spawnvp", "exec", "eval"}
    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name.split(".")[0] in forbidden_modules for alias in node.names):
                    raise ContractError(f"forbidden process module import in {path.name}")
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in forbidden_modules:
                raise ContractError(f"forbidden process module import in {path.name}")
            elif isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name.lower() in forbidden_calls:
                    raise ContractError(f"forbidden execution call {name} in {path.name}")


def _verify_plan(plan: dict[str, Any]) -> None:
    if plan.get("execution_allowed") is not False or plan.get("generator_executed_commands") is not False:
        raise ContractError("emulation plan must fail closed")
    if plan.get("production_ready") is not False:
        raise ContractError("emulation plan cannot claim production readiness")
    actions = plan.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ContractError("emulation plan must contain inert actions")
    for action in actions:
        argv = action.get("argv") if isinstance(action, dict) else None
        if not isinstance(argv, list) or not argv or argv[0] not in {"ip", "tc"}:
            raise ContractError("each plan action must be a structured, allowlisted argv record")
        for token in argv:
            if not isinstance(token, str) or any(character in token for character in "\n\r\x00;|&`$<>"):
                raise ContractError("unsafe token in inert argv record")


def verify_all() -> None:
    validate_scenario(load_json(DATASETS, "scenario.json"))
    validate_routing_replay(load_json(DATASETS, "routing_replay.json"))
    validate_calibration_trace(load_json(DATASETS, "calibration_trace.json"))
    validate_emulation_request(load_json(DATASETS, "emulation_request.json"))

    for schema_path in sorted((ROOT / "schemas").glob("*.json")):
        schema = _load_json_file(schema_path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ContractError(f"unexpected schema dialect: {schema_path.name}")

    expected_result, expected_plan = build_artifacts()
    actual_result = _load_json_file(RESULT_PATH)
    actual_plan = _load_json_file(PLAN_PATH)
    if canonical_json(actual_result) != canonical_json(expected_result):
        raise ContractError("committed benchmark results are stale")
    if canonical_json(actual_plan) != canonical_json(expected_plan):
        raise ContractError("committed emulation plan is stale")
    if actual_result.get("synthetic") is not True or actual_result.get("production_evidence") is not False:
        raise ContractError("result classification must remain synthetic and non-production")
    if len(actual_result.get("seeds", [])) < 3 or not actual_result.get("negative_findings"):
        raise ContractError("results need multiple seeds and explicit negative findings")
    _verify_plan(actual_plan)
    _verify_python_boundary()
    verify_notebooks()

    actual_manifest = _load_json_file(MANIFEST_PATH)
    expected_manifest = build_manifest()
    if canonical_json(actual_manifest) != canonical_json(expected_manifest):
        raise ContractError("manifest is stale; run verify --write-manifest")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="regenerate only the deterministic SHA-256 manifest before checking",
    )
    arguments = parser.parse_args()
    if arguments.write_manifest:
        MANIFEST_PATH.write_text(canonical_json(build_manifest()), encoding="utf-8")
    verify_all()
    print("verified datasets, results, schemas, security boundary, and SHA-256 manifest")


if __name__ == "__main__":
    main()
