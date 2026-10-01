"""Build or check the committed deterministic lab results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .contracts import (
    load_json,
    validate_calibration_trace,
    validate_emulation_request,
    validate_routing_replay,
    validate_scenario,
)
from .simulator import (
    calibrate_queue_model,
    generate_emulation_plan,
    replay_routing,
    simulate_impairments,
    simulate_queue,
    summarize,
)


ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "datasets"
RESULTS = ROOT / "results"
RESULT_PATH = RESULTS / "benchmark_results.json"
PLAN_PATH = RESULTS / "emulation_plan.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    scenario = validate_scenario(load_json(DATASETS, "scenario.json"))
    routing = validate_routing_replay(load_json(DATASETS, "routing_replay.json"))
    calibration_trace = validate_calibration_trace(load_json(DATASETS, "calibration_trace.json"))
    emulation_request = validate_emulation_request(load_json(DATASETS, "emulation_request.json"))

    seeds = list(scenario["seeds"])
    queue_runs = [simulate_queue(scenario["queue"], seed) for seed in seeds]
    impairment_runs = [simulate_impairments(scenario["impairments"], seed) for seed in seeds]
    routing_result = replay_routing(routing)
    calibration_result = calibrate_queue_model(calibration_trace)
    plan = generate_emulation_plan(emulation_request)

    queue_summary = {
        metric: summarize(run[metric] for run in queue_runs)
        for metric in (
            "drop_rate",
            "mean_response_ms",
            "p95_response_ms",
            "throughput_pps",
            "server_utilization",
            "drain_time_ms",
        )
    }
    impairment_summary = {
        metric: summarize(run[metric] for run in impairment_runs)
        for metric in (
            "observed_loss_rate",
            "observed_duplicate_rate",
            "observed_reorder_rate",
            "mean_delay_ms",
            "p95_delay_ms",
        )
    }

    negative_findings = [
        {
            "id": "queue_tail_variance",
            "evidence": (
                f"Across {len(seeds)} fixed seeds, p95 response ranged from "
                f"{queue_summary['p95_response_ms']['minimum']} to "
                f"{queue_summary['p95_response_ms']['maximum']} ms."
            ),
            "implication": "A mean-only queue claim hides material tail and seed sensitivity.",
        },
        {
            "id": "impairments_interact",
            "evidence": (
                f"The synthetic flow produced a mean reorder rate of "
                f"{impairment_summary['observed_reorder_rate']['mean']} after delay jitter, "
                "independently of the configured loss probability."
            ),
            "implication": "Loss, duplication, jitter, and ordering must be reported separately.",
        },
        {
            "id": "routing_blackhole_window",
            "evidence": (
                f"Event replay retained an invalid path for "
                f"{routing_result['total_transient_blackhole_ms']} ms before control-plane application."
            ),
            "implication": "A converged shortest path does not prove transient reachability.",
        },
        {
            "id": "calibration_coverage_failure",
            "evidence": (
                f"The train-residual interval covered only "
                f"{calibration_result['holdout_interval_coverage']:.3f} of held-out observations; "
                f"OOD MAE was {calibration_result['ood_mae_ms']:.3f} ms."
            ),
            "implication": "In-range calibration cannot justify high-load extrapolation.",
        },
        {
            "id": "emulation_not_executed",
            "evidence": "The generated artifact contains inert argv arrays and execution_allowed=false.",
            "implication": "The plan is teaching material, not privileged emulation evidence.",
        },
    ]

    result = {
        "schema_version": "1.0",
        "suite": "offline-synthetic-network-simulation",
        "synthetic": True,
        "production_evidence": False,
        "seeds": seeds,
        "queue": {"runs": queue_runs, "summary": queue_summary},
        "packet_impairments": {"runs": impairment_runs, "summary": impairment_summary},
        "routing_replay": routing_result,
        "calibration": calibration_result,
        "emulation_plan": {
            "artifact": "results/emulation_plan.json",
            "execution_allowed": False,
            "generator_executed_commands": False,
        },
        "negative_findings": negative_findings,
    }
    return result, plan


def check_artifacts() -> None:
    result, plan = build_artifacts()
    expected = {RESULT_PATH: canonical_json(result), PLAN_PATH: canonical_json(plan)}
    mismatches = []
    for path, content in expected.items():
        try:
            current = path.read_text(encoding="utf-8")
        except OSError:
            mismatches.append(f"missing {path.relative_to(ROOT)}")
            continue
        if current != content:
            mismatches.append(f"stale {path.relative_to(ROOT)}")
    if mismatches:
        raise SystemExit("; ".join(mismatches) + "; run with --write")


def write_artifacts() -> None:
    result, plan = build_artifacts()
    RESULTS.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(canonical_json(result), encoding="utf-8")
    PLAN_PATH.write_text(canonical_json(plan), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if committed results differ")
    mode.add_argument("--write", action="store_true", help="regenerate committed results only")
    arguments = parser.parse_args()
    if arguments.write:
        write_artifacts()
        print("wrote deterministic synthetic results; no command was executed")
    else:
        check_artifacts()
        print("deterministic synthetic results match")


if __name__ == "__main__":
    main()
