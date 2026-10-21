"""Generate retained, multi-seed ML/RL evidence for the book laboratories."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
from statistics import fmean, stdev
from typing import Any

from dqn_relay_lab import (
    DQNConfig,
    always_relay_a_policy,
    dqn_policy,
    evaluate_policy,
    projected_queue_policy,
    random_policy,
    train_dqn,
)
from rare_classification_lab import run_experiment


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
JSON_PATH = RESULTS_DIR / "benchmark_results.json"
CSV_PATH = RESULTS_DIR / "benchmark_summary.csv"
TRAINING_SEEDS = (7, 19, 31, 43, 59)
EVALUATION_SEEDS = tuple(range(1_000, 1_040))
T95_DF4 = 2.7764451051977987


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_rounded(item) for item in value]
    return value


def _summary(values: list[float]) -> dict[str, object]:
    if len(values) != len(TRAINING_SEEDS):
        raise ValueError("reference uncertainty requires the five training seeds")
    sample_stddev = stdev(values)
    return {
        "per_training_seed": {
            str(seed): value for seed, value in zip(TRAINING_SEEDS, values, strict=True)
        },
        "mean": fmean(values),
        "sample_stddev": sample_stddev,
        "ci95_half_width": T95_DF4 * sample_stddev / math.sqrt(len(values)),
    }


def build_results(*, episodes: int = 180) -> dict[str, object]:
    classification = run_experiment()
    baseline_random = evaluate_policy(random_policy, seeds=EVALUATION_SEEDS)
    baseline_projected = evaluate_policy(
        projected_queue_policy, seeds=EVALUATION_SEEDS
    )
    safety_probe = evaluate_policy(
        always_relay_a_policy,
        seeds=EVALUATION_SEEDS,
        drop_termination_threshold=None,
    )
    runs: list[dict[str, object]] = []
    for seed in TRAINING_SEEDS:
        config = DQNConfig(seed=seed, episodes=episodes)
        training = train_dqn(config)
        evaluation = evaluate_policy(
            dqn_policy(training.model),
            seeds=EVALUATION_SEEDS,
            horizon=config.horizon,
            drop_termination_threshold=config.drop_termination_threshold,
        )
        runs.append(
            {
                "training_seed": seed,
                "training": training.metadata(),
                "evaluation": evaluation,
                "paired_delta_vs_random": {
                    "mean_return": evaluation["mean_return"]
                    - baseline_random["mean_return"],
                    "mean_dropped": evaluation["mean_dropped"]
                    - baseline_random["mean_dropped"],
                },
                "paired_delta_vs_projected_queue": {
                    "mean_return": evaluation["mean_return"]
                    - baseline_projected["mean_return"],
                    "mean_dropped": evaluation["mean_dropped"]
                    - baseline_projected["mean_dropped"],
                },
            }
        )

    def values(path: tuple[str, ...]) -> list[float]:
        selected: list[float] = []
        for run in runs:
            item: Any = run
            for key in path:
                item = item[key]
            selected.append(float(item))
        return selected

    dqn_summary = {
        metric: _summary(values(("evaluation", metric)))
        for metric in (
            "mean_return",
            "mean_dropped",
            "mean_delivered",
            "blocked_proposal_rate",
        )
    }
    paired_summary = {
        baseline: {
            metric: _summary(values((field, metric)))
            for metric in ("mean_return", "mean_dropped")
        }
        for baseline, field in (
            ("random", "paired_delta_vs_random"),
            ("projected_queue", "paired_delta_vs_projected_queue"),
        )
    }
    all_applied_violations = sum(
        float(run["evaluation"]["applied_constraint_violations"])  # type: ignore[index]
        for run in runs
    )
    negative_findings: list[str] = []
    projected_return_delta = float(
        paired_summary["projected_queue"]["mean_return"]["mean"]  # type: ignore[index]
    )
    if projected_return_delta <= 0.0:
        negative_findings.append(
            "The model-informed projected-queue reference has higher mean return "
            "than the DQN mean; added learning complexity is not universally superior."
        )
    projected_drop_delta = float(
        paired_summary["projected_queue"]["mean_dropped"]["mean"]  # type: ignore[index]
    )
    if projected_drop_delta >= 0.0:
        negative_findings.append(
            "The DQN mean does not reduce dropped packets relative to the "
            "projected-queue reference."
        )

    results = {
        "schema_version": "1.0.0",
        "benchmark_id": "network-book-ml-rl-evidence-v1",
        "evidence_scope": {
            "kind": "deterministic_synthetic",
            "production_proof": False,
            "statement": (
                "Pedagogical evidence only; no RF, transport, field, mission, "
                "or production-performance claim."
            ),
        },
        "training_seeds": list(TRAINING_SEEDS),
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "uncertainty_method": (
            "two-sided Student-t 95% confidence interval across five independent "
            "training seeds (df=4); evaluation scenarios are paired"
        ),
        "controller_information_contract": (
            "Every policy receives only the seven-element observation and a seeded RNG."
        ),
        "baselines": {
            "random_available": baseline_random,
            "projected_queue_observation_only": baseline_projected,
        },
        "dqn_runs": runs,
        "dqn_summary": dqn_summary,
        "paired_summary": paired_summary,
        "hard_constraint_probe": {
            "policy": "always_propose_relay_a",
            "result": safety_probe,
            "criterion": "blocked proposals may be nonzero; applied violations must be zero",
        },
        "rare_classification": classification,
        "success_criteria": {
            "multiple_training_seeds": len(runs) == 5,
            "paired_return_ci_reported": math.isfinite(
                float(
                    paired_summary["random"]["mean_return"][  # type: ignore[index]
                        "ci95_half_width"
                    ]
                )
            ),
            "paired_drop_ci_reported": math.isfinite(
                float(
                    paired_summary["random"]["mean_dropped"][  # type: ignore[index]
                        "ci95_half_width"
                    ]
                )
            ),
            "zero_applied_constraint_violations": all_applied_violations == 0.0
            and safety_probe["applied_constraint_violations"] == 0.0,
            "filter_blocks_unsafe_proposals": safety_probe["mean_blocked_proposals"]
            > 0.0,
            "classification_test_opened_once": classification["split_contract"][  # type: ignore[index]
                "test_open_count"
            ]
            == 1,
        },
        "negative_findings": negative_findings,
    }
    if not all(results["success_criteria"].values()):  # type: ignore[union-attr]
        raise AssertionError(f"benchmark criteria failed: {results['success_criteria']}")
    return _rounded(results)


def render_json(results: dict[str, object]) -> str:
    return json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_csv(results: dict[str, object]) -> str:
    output = io.StringIO(newline="")
    fields = (
        "training_seed",
        "policy",
        "mean_return",
        "return_std",
        "mean_dropped",
        "mean_delivered",
        "blocked_proposal_rate",
        "applied_constraint_violations",
    )
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    baselines = results["baselines"]  # type: ignore[assignment]
    for name, metrics in baselines.items():  # type: ignore[union-attr]
        writer.writerow({"training_seed": "", "policy": name, **metrics})
    for run in results["dqn_runs"]:  # type: ignore[union-attr]
        writer.writerow(
            {
                "training_seed": run["training_seed"],
                "policy": "dqn",
                **run["evaluation"],
            }
        )
    return output.getvalue().replace("\r\n", "\n")


def write_or_check(*, check: bool) -> dict[str, object]:
    results = build_results()
    expected = {JSON_PATH: render_json(results), CSV_PATH: render_csv(results)}
    if check:
        for path, content in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise AssertionError(f"stale benchmark artifact: {path}")
    else:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        for path, content in expected.items():
            path.write_text(content, encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    results = write_or_check(check=args.check)
    print(json.dumps(results["success_criteria"], sort_keys=True))


if __name__ == "__main__":
    main()
