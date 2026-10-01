"""Run the retained L24 packet-drop-constrained DQN experiment."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, Iterable

from dqn_relay_lab import (
    DQNConfig,
    dqn_policy,
    evaluate_policy,
    projected_queue_policy,
    random_policy,
    train_dqn,
)
from run_benchmarks import EVALUATION_SEEDS, T95_DF4, TRAINING_SEEDS


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
JSON_PATH = RESULTS_DIR / "constrained_dqn_results.json"
CSV_PATH = RESULTS_DIR / "constrained_dqn_summary.csv"
DEFAULT_TRAINING_DROP_PENALTIES = (4.0, 6.0, 8.0, 12.0, 16.0)
REPORTING_DROP_PENALTY = 4.0


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
        raise ValueError("L24 uncertainty requires the five canonical training seeds")
    sample_stddev = stdev(values)
    return {
        "per_training_seed": {
            str(seed): value for seed, value in zip(TRAINING_SEEDS, values, strict=True)
        },
        "mean": fmean(values),
        "sample_stddev": sample_stddev,
        "ci95_half_width": T95_DF4 * sample_stddev / math.sqrt(len(values)),
    }


def acceptance_gate(
    paired_vs_random: dict[str, dict[str, object]],
    *,
    applied_constraint_violations: float,
    baseline: str = "random_available",
) -> dict[str, object]:
    """Apply the predeclared L24 gate without hiding a negative result."""

    return_summary = paired_vs_random["mean_return"]
    drop_summary = paired_vs_random["mean_dropped"]
    return_lower_bound = float(return_summary["mean"]) - float(
        return_summary["ci95_half_width"]
    )
    drop_upper_bound = float(drop_summary["mean"]) + float(
        drop_summary["ci95_half_width"]
    )
    criteria = {
        "zero_applied_constraint_violations": applied_constraint_violations == 0.0,
        "no_drop_regression_at_95pct": drop_upper_bound <= 0.0,
        "positive_return_improvement_at_95pct": return_lower_bound > 0.0,
    }
    return {
        "baseline": baseline,
        "confidence_level": 0.95,
        "return_delta_lower_bound": return_lower_bound,
        "drop_delta_upper_bound": drop_upper_bound,
        "criteria": criteria,
        "passes": all(criteria.values()),
    }


def _candidate_rank(
    candidate: dict[str, object], *, gate_name: str = "acceptance_gate"
) -> tuple[float, float, float]:
    gate = candidate[gate_name]  # type: ignore[assignment]
    return (
        float(gate["drop_delta_upper_bound"]),  # type: ignore[index]
        -float(gate["return_delta_lower_bound"]),  # type: ignore[index]
        float(candidate["training_drop_penalty"]),
    )


def build_results(
    *,
    episodes: int = 180,
    training_drop_penalties: Iterable[float] = DEFAULT_TRAINING_DROP_PENALTIES,
) -> dict[str, object]:
    penalties = tuple(float(value) for value in training_drop_penalties)
    if not penalties:
        raise ValueError("at least one training drop penalty is required")
    if any(not math.isfinite(value) or value < 0.0 for value in penalties):
        raise ValueError("training drop penalties must be finite and non-negative")
    if len(set(penalties)) != len(penalties):
        raise ValueError("training drop penalties must be unique")

    baseline_random = evaluate_policy(
        random_policy,
        seeds=EVALUATION_SEEDS,
        drop_penalty=REPORTING_DROP_PENALTY,
    )
    baseline_projected = evaluate_policy(
        projected_queue_policy,
        seeds=EVALUATION_SEEDS,
        drop_penalty=REPORTING_DROP_PENALTY,
    )
    baselines = {
        "random_available": baseline_random,
        "projected_queue_observation_only": baseline_projected,
    }

    candidates: list[dict[str, object]] = []
    for penalty in penalties:
        runs: list[dict[str, object]] = []
        for seed in TRAINING_SEEDS:
            config = DQNConfig(
                seed=seed,
                episodes=episodes,
                drop_penalty=penalty,
            )
            training = train_dqn(config)
            evaluation = evaluate_policy(
                dqn_policy(training.model),
                seeds=EVALUATION_SEEDS,
                horizon=config.horizon,
                drop_termination_threshold=config.drop_termination_threshold,
                drop_penalty=REPORTING_DROP_PENALTY,
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

        evaluation_summary = {
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
        all_violations = sum(
            float(run["evaluation"]["applied_constraint_violations"])  # type: ignore[index]
            for run in runs
        )
        candidates.append(
            {
                "training_drop_penalty": penalty,
                "reporting_drop_penalty": REPORTING_DROP_PENALTY,
                "runs": runs,
                "evaluation_summary": evaluation_summary,
                "paired_summary": paired_summary,
                "acceptance_gate": acceptance_gate(
                    paired_summary["random"],
                    applied_constraint_violations=all_violations,
                ),
                "projected_queue_gate": acceptance_gate(
                    paired_summary["projected_queue"],
                    applied_constraint_violations=all_violations,
                    baseline="projected_queue_observation_only",
                ),
            }
        )

    accepted = [
        candidate
        for candidate in candidates
        if bool(candidate["acceptance_gate"]["passes"])  # type: ignore[index]
    ]
    best_candidate = min(accepted or candidates, key=_candidate_rank)
    accepted_penalties = [
        float(candidate["training_drop_penalty"]) for candidate in accepted
    ]
    accepted_vs_projected = [
        candidate
        for candidate in candidates
        if bool(candidate["projected_queue_gate"]["passes"])  # type: ignore[index]
    ]
    accepted_vs_projected_penalties = [
        float(candidate["training_drop_penalty"]) for candidate in accepted_vs_projected
    ]
    if accepted_vs_projected:
        reference_best = min(
            accepted_vs_projected,
            key=lambda candidate: _candidate_rank(
                candidate, gate_name="projected_queue_gate"
            ),
        )
        preferred_controller = (
            f"dqn_training_drop_penalty_{reference_best['training_drop_penalty']:g}"
        )
        conclusion = (
            "At least one DQN configuration passes the return, packet-drop, and "
            "hard-safety gate against both paired baselines."
        )
    elif accepted:
        preferred_controller = "projected_queue_observation_only"
        conclusion = (
            "The selected DQN configuration passes the predeclared random-baseline "
            "gate but does not robustly dominate the projected-load heuristic; the "
            "simpler heuristic remains preferable for this synthetic scenario."
        )
    else:
        preferred_controller = "projected_queue_observation_only"
        conclusion = (
            "No DQN configuration passes the predeclared gate; the projected-load "
            "heuristic remains preferable for this synthetic scenario."
        )

    results = {
        "schema_version": "1.0.0",
        "experiment_id": "network-book-l24-constrained-dqn-v1",
        "question": (
            "Can packet-drop-aware DQN training remove the observed drop regression "
            "without sacrificing a statistically positive return gain?"
        ),
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
        "training_drop_penalties": list(penalties),
        "reporting_drop_penalty": REPORTING_DROP_PENALTY,
        "uncertainty_method": (
            "two-sided Student-t 95% confidence interval across five independent "
            "training seeds (df=4); held-out evaluation scenarios are paired"
        ),
        "objective": (
            "Sweep the training packet-drop penalty, then select lexicographically "
            "by the random-baseline drop upper bound, return lower bound, and "
            "smaller penalty. Evaluation always uses the canonical reward."
        ),
        "acceptance_contract": {
            "baseline": "random_available",
            "zero_applied_constraint_violations": True,
            "maximum_drop_delta_upper_95pct": 0.0,
            "minimum_return_delta_lower_95pct_exclusive": 0.0,
        },
        "baselines": baselines,
        "candidates": candidates,
        "selection": {
            "accepted_training_drop_penalties": accepted_penalties,
            "accepted_vs_projected_queue_penalties": (accepted_vs_projected_penalties),
            "best_candidate_training_drop_penalty": float(
                best_candidate["training_drop_penalty"]
            ),
            "preferred_controller": preferred_controller,
            "conclusion": conclusion,
        },
        "success_criteria": {
            "five_canonical_training_seeds": len(TRAINING_SEEDS) == 5,
            "forty_paired_evaluation_seeds": len(EVALUATION_SEEDS) == 40,
            "all_penalties_evaluated": len(candidates) == len(penalties),
            "all_candidates_respect_hard_filter": all(
                bool(
                    candidate["acceptance_gate"]["criteria"][  # type: ignore[index]
                        "zero_applied_constraint_violations"
                    ]
                )
                for candidate in candidates
            ),
            "scientific_outcome_retained_even_if_negative": True,
        },
    }
    if not all(results["success_criteria"].values()):  # type: ignore[union-attr]
        raise AssertionError(
            f"L24 experiment criteria failed: {results['success_criteria']}"
        )
    return _rounded(results)


def render_json(results: dict[str, object]) -> str:
    return json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_csv(results: dict[str, object]) -> str:
    output = io.StringIO(newline="")
    fields = (
        "training_drop_penalty",
        "training_seed",
        "policy",
        "mean_return",
        "mean_dropped",
        "mean_delivered",
        "applied_constraint_violations",
        "return_delta_vs_random",
        "drop_delta_vs_random",
        "return_delta_vs_projected_queue",
        "drop_delta_vs_projected_queue",
    )
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for name, metrics in results["baselines"].items():  # type: ignore[union-attr]
        writer.writerow(
            {
                "training_drop_penalty": "",
                "training_seed": "",
                "policy": name,
                **{
                    key: metrics[key]  # type: ignore[index]
                    for key in (
                        "mean_return",
                        "mean_dropped",
                        "mean_delivered",
                        "applied_constraint_violations",
                    )
                },
            }
        )
    for candidate in results["candidates"]:  # type: ignore[union-attr]
        for run in candidate["runs"]:  # type: ignore[index]
            evaluation = run["evaluation"]
            versus_random = run["paired_delta_vs_random"]
            versus_projected = run["paired_delta_vs_projected_queue"]
            writer.writerow(
                {
                    "training_drop_penalty": candidate["training_drop_penalty"],
                    "training_seed": run["training_seed"],
                    "policy": "dqn",
                    "mean_return": evaluation["mean_return"],
                    "mean_dropped": evaluation["mean_dropped"],
                    "mean_delivered": evaluation["mean_delivered"],
                    "applied_constraint_violations": evaluation[
                        "applied_constraint_violations"
                    ],
                    "return_delta_vs_random": versus_random["mean_return"],
                    "drop_delta_vs_random": versus_random["mean_dropped"],
                    "return_delta_vs_projected_queue": versus_projected["mean_return"],
                    "drop_delta_vs_projected_queue": versus_projected["mean_dropped"],
                }
            )
    return output.getvalue().replace("\r\n", "\n")


def write_or_check(*, check: bool) -> dict[str, object]:
    results = build_results()
    expected = {JSON_PATH: render_json(results), CSV_PATH: render_csv(results)}
    if check:
        for path, content in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise AssertionError(f"stale L24 experiment artifact: {path}")
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
    print(json.dumps(results["selection"], sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
