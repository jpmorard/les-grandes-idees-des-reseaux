"""Generate deterministic core-network lab evidence, or verify retained evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .models import (
    Packet,
    apply_origin_policy,
    classify_origin,
    convergence_case,
    simulate_queue,
)

ROOT = Path(__file__).resolve().parent
SCENARIO = ROOT / "inputs" / "scenarios.json"
RESULT_NAMES = ("latency_qos.json", "convergence.json", "bgp_rov.json")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_results() -> dict[str, dict[str, Any]]:
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    if scenario["schema"] != "network-book.core-labs.scenarios.v1":
        raise ValueError("unsupported scenario schema")
    queue = scenario["queue"]
    packets = [
        Packet(f"bulk-{i:04d}", "bulk", arrival, queue["bulk_size_bytes"], 1)
        for i, arrival in enumerate(
            range(0, queue["duration_us"], queue["bulk_interval_us"])
        )
    ] + [
        Packet(f"voice-{i:04d}", "voice", arrival, queue["voice_size_bytes"], 0)
        for i, arrival in enumerate(
            range(0, queue["duration_us"], queue["voice_interval_us"])
        )
    ]
    queue_cases = {}
    for name, capacity, policy in (
        ("fifo_small", queue["small_waiting_slots"], "fifo"),
        ("fifo_large", queue["large_waiting_slots"], "fifo"),
        ("priority_large", queue["large_waiting_slots"], "priority"),
    ):
        queue_cases[name] = simulate_queue(
            packets, rate_bps=queue["rate_bps"], waiting_slots=capacity, policy=policy
        )
    conv = scenario["convergence"]
    convergence = {
        name: convergence_case(
            conv["edges"],
            failed_link=tuple(conv["failed_link"]),
            updates_ms=conv[f"{name}_updates_ms"],
            probes_ms=conv["probes_ms"],
        )
        for name in ("unordered", "ordered")
    }
    rov = scenario["rov"]
    rows = []
    for route in rov["routes"]:
        state = classify_origin(route["prefix"], route["origin_as"], rov["vrps"])
        rows.append(
            {
                **route,
                "validation_state": state,
                "classification_only": apply_origin_policy(state, reject_invalid=False),
                "reject_invalid_policy": apply_origin_policy(
                    state, reject_invalid=True
                ),
            }
        )
    unavailable = classify_origin(
        "203.0.113.0/24", 64500, rov["vrps"], cache_available=False
    )
    common = {
        "schema": "network-book.core-labs.result.v1",
        "evidence_scope": "deterministic_synthetic_teaching_model_not_real_protocol_execution",
        "scenario_sha256": sha256(SCENARIO),
        "producer": "python3 -m core_network_labs.run_labs",
        "time_resolution": "integer microseconds for queue; integer milliseconds for FIB events",
    }
    return {
        "latency_qos.json": {
            **common,
            "experiment": "queue_capacity_and_service_order",
            "cases": queue_cases,
        },
        "convergence.json": {
            **common,
            "experiment": "asynchronous_fib_installation",
            "cases": convergence,
        },
        "bgp_rov.json": {
            **common,
            "experiment": "origin_validation_vs_configured_policy",
            "routes": rows,
            "cache_unavailable": {
                "validation_state": unavailable,
                "declared_local_policy": apply_origin_policy(
                    unavailable, reject_invalid=True
                ),
            },
        },
    }


def source_paths() -> list[Path]:
    paths = [
        ROOT / "__init__.py",
        ROOT / "models.py",
        ROOT / "premiers_pas_reseaux_fr.py",
        ROOT / "run_labs.py",
        ROOT / "verify_notebooks.py",
        ROOT / "README.md",
        SCENARIO,
    ]
    paths += sorted((ROOT / "notebooks").glob("*.ipynb"))
    paths += sorted((ROOT / "tests").glob("test_*.py"))
    return paths


def build_manifest(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    files = [
        {
            "path": str(p.relative_to(ROOT)),
            "size_bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        for p in source_paths()
    ]
    for name, artifact in sorted(artifacts.items()):
        content = canonical_json(artifact).encode("utf-8")
        files.append(
            {
                "path": f"results/{name}",
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return {
        "schema": "network-book.core-labs.manifest.v1",
        "root": ".",
        "producer": "python3 -m core_network_labs.run_labs",
        "runtime_contract": "Python >= 3.10; standard library; deterministic integer event times",
        "notebook_environment": {
            "root": "..",
            "project": "machine_learning_labs/pyproject.toml",
            "project_sha256": sha256(
                ROOT.parent / "machine_learning_labs" / "pyproject.toml"
            ),
            "lock": "machine_learning_labs/uv.lock",
            "lock_sha256": sha256(ROOT.parent / "machine_learning_labs" / "uv.lock"),
        },
        "evidence_scope": "synthetic; no interfaces configured; no packets transmitted",
        "files": files,
    }


def check_artifacts(root: Path = ROOT) -> None:
    artifacts = build_results()
    expected = {
        f"results/{name}": canonical_json(result) for name, result in artifacts.items()
    }
    expected["manifest.json"] = canonical_json(build_manifest(artifacts))
    stale = [
        name
        for name, text in expected.items()
        if not (root / name).is_file()
        or (root / name).read_text(encoding="utf-8") != text
    ]
    if stale:
        raise SystemExit("Core network evidence missing/stale: " + ", ".join(stale))
    print(
        "Core network labs: PASS (3 deterministic experiments; sources and results hashed)"
    )


def write_artifacts(output: Path) -> None:
    artifacts = build_results()
    output.mkdir(parents=True, exist_ok=True)
    for name, result in artifacts.items():
        (output / name).write_text(canonical_json(result), encoding="utf-8")
    if output.resolve() == (ROOT / "results").resolve():
        (ROOT / "manifest.json").write_text(
            canonical_json(build_manifest(artifacts)), encoding="utf-8"
        )
    print(
        f"Core network labs: wrote {len(artifacts)} synthetic result files to {output}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="read-only retained evidence check"
    )
    mode.add_argument(
        "--output", type=Path, help="write only result files in this directory"
    )
    args = parser.parse_args()
    if args.check:
        check_artifacts()
    else:
        write_artifacts(args.output or ROOT / "results")


if __name__ == "__main__":
    main()
