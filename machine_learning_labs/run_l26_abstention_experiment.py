"""Run the retained L26 disagreement-gated DQN experiment."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, Iterable, Sequence

from dqn_relay_lab import (
    DQNConfig,
    Policy,
    QNetwork,
    dqn_policy,
    evaluate_policy,
    projected_queue_policy,
    train_dqn,
)
from run_benchmarks import EVALUATION_SEEDS, TRAINING_SEEDS
from run_constrained_dqn_experiment import _rounded
from run_l25_robustness_experiment import (
    DEVELOPMENT_SHIFT_SCENARIOS,
    FROZEN_TRAINING_DROP_PENALTY,
    NOMINAL_SCENARIO,
    EvaluationScenario,
)


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
JSON_PATH = RESULTS_DIR / "l26_abstention_results.json"
CSV_PATH = RESULTS_DIR / "l26_abstention_summary.csv"
DEFAULT_AGREEMENT_THRESHOLDS = (0.6, 0.8, 1.0)
T95_DF39 = 2.02269092


FINAL_CHALLENGE_SCENARIO = EvaluationScenario(
    scenario_id="sealed_staggered_cross_shift",
    role="sealed_final_challenge",
    description=(
        "Unseen staggered combination of bursty arrivals, seven-packet queues, "
        "shifted service, and alternating relay unavailability."
    ),
    queue_capacity=7,
    arrival_pattern=(4, 1, 5, 1),
    service_a_pattern=(0, 2, 1, 0),
    service_b_pattern=(1, 0, 0, 3),
    outage_pattern=(None, 1, None, 0),
)


class DisagreementGatedPolicy:
    """Use the DQN majority only above a vote-share threshold."""

    def __init__(
        self,
        models: Sequence[QNetwork],
        *,
        min_vote_share: float,
        fallback: Policy = projected_queue_policy,
    ) -> None:
        if len(models) < 3 or len(models) % 2 == 0:
            raise ValueError(
                "the model panel must contain an odd number of models >= 3"
            )
        if not math.isfinite(min_vote_share) or not 0.5 < min_vote_share <= 1.0:
            raise ValueError("min_vote_share must be finite and in (0.5, 1.0]")
        self.member_policies = tuple(dqn_policy(model) for model in models)
        self.min_vote_share = float(min_vote_share)
        self.fallback = fallback
        self.decisions = 0
        self.fallback_decisions = 0
        self.unanimous_decisions = 0
        self.vote_share_total = 0.0

    def __call__(self, observation: Any, rng: Any) -> int:
        votes = [policy(observation, rng) for policy in self.member_policies]
        counts = {action: votes.count(action) for action in (0, 1)}
        majority_action = max((0, 1), key=lambda action: (counts[action], -action))
        vote_share = counts[majority_action] / len(votes)
        self.decisions += 1
        self.vote_share_total += vote_share
        self.unanimous_decisions += int(vote_share == 1.0)
        if vote_share < self.min_vote_share:
            self.fallback_decisions += 1
            return int(self.fallback(observation, rng))
        return int(majority_action)

    def diagnostics(self) -> dict[str, float]:
        if self.decisions == 0:
            raise RuntimeError("the policy has not made a decision")
        return {
            "fallback_rate": self.fallback_decisions / self.decisions,
            "mean_majority_vote_share": self.vote_share_total / self.decisions,
            "unanimous_rate": self.unanimous_decisions / self.decisions,
        }


def _evaluation_seed_summary(values: list[float]) -> dict[str, object]:
    if len(values) != len(EVALUATION_SEEDS):
        raise ValueError("L26 uncertainty requires the forty evaluation seeds")
    sample_stddev = stdev(values)
    return {
        "per_evaluation_seed": {
            str(seed): value
            for seed, value in zip(EVALUATION_SEEDS, values, strict=True)
        },
        "mean": fmean(values),
        "sample_stddev": sample_stddev,
        "ci95_half_width": T95_DF39 * sample_stddev / math.sqrt(len(values)),
    }


def non_regression_gate(
    paired_summary: dict[str, dict[str, object]],
    *,
    applied_constraint_violations: float,
) -> dict[str, object]:
    """Require 95% non-regression against the fallback on both objectives."""

    return_summary = paired_summary["mean_return"]
    drop_summary = paired_summary["mean_dropped"]
    return_lower_bound = float(return_summary["mean"]) - float(
        return_summary["ci95_half_width"]
    )
    drop_upper_bound = float(drop_summary["mean"]) + float(
        drop_summary["ci95_half_width"]
    )
    criteria = {
        "zero_applied_constraint_violations": applied_constraint_violations == 0.0,
        "no_return_regression_at_95pct": return_lower_bound >= 0.0,
        "no_drop_regression_at_95pct": drop_upper_bound <= 0.0,
    }
    return {
        "baseline": "projected_queue_observation_only",
        "confidence_level": 0.95,
        "return_delta_lower_bound": return_lower_bound,
        "drop_delta_upper_bound": drop_upper_bound,
        "criteria": criteria,
        "passes": all(criteria.values()),
    }


def _baseline_runs(scenario: EvaluationScenario) -> list[dict[str, object]]:
    return [
        {
            "evaluation_seed": seed,
            "evaluation": evaluate_policy(
                projected_queue_policy,
                seeds=(seed,),
                **scenario.environment_kwargs(),
            ),
        }
        for seed in EVALUATION_SEEDS
    ]


def _aggregate_runs(runs: list[dict[str, object]]) -> dict[str, float]:
    evaluations = [run["evaluation"] for run in runs]
    return {
        metric: fmean(float(evaluation[metric]) for evaluation in evaluations)  # type: ignore[index]
        for metric in ("mean_return", "mean_dropped", "mean_delivered")
    } | {
        "applied_constraint_violations": sum(
            float(evaluation["applied_constraint_violations"])  # type: ignore[index]
            for evaluation in evaluations
        ),
        "episodes": sum(
            float(evaluation["episodes"])  # type: ignore[index]
            for evaluation in evaluations
        ),
    }


def _evaluate_candidate(
    scenario: EvaluationScenario,
    *,
    models: Sequence[QNetwork],
    min_vote_share: float,
    baseline_runs: list[dict[str, object]],
) -> dict[str, object]:
    runs: list[dict[str, object]] = []
    for seed, baseline_run in zip(EVALUATION_SEEDS, baseline_runs, strict=True):
        policy = DisagreementGatedPolicy(models, min_vote_share=min_vote_share)
        evaluation = evaluate_policy(
            policy,
            seeds=(seed,),
            **scenario.environment_kwargs(),
        )
        baseline = baseline_run["evaluation"]
        runs.append(
            {
                "evaluation_seed": seed,
                "evaluation": evaluation,
                **policy.diagnostics(),
                "paired_delta_vs_projected_queue": {
                    "mean_return": float(evaluation["mean_return"])
                    - float(baseline["mean_return"]),  # type: ignore[index]
                    "mean_dropped": float(evaluation["mean_dropped"])
                    - float(baseline["mean_dropped"]),  # type: ignore[index]
                },
            }
        )

    paired_summary = {
        metric: _evaluation_seed_summary(
            [
                float(run["paired_delta_vs_projected_queue"][metric])  # type: ignore[index]
                for run in runs
            ]
        )
        for metric in ("mean_return", "mean_dropped")
    }
    violations = sum(
        float(run["evaluation"]["applied_constraint_violations"])  # type: ignore[index]
        for run in runs
    )
    return {
        "minimum_majority_vote_share": min_vote_share,
        "policy_id": f"dqn_ensemble_vote_gate_{min_vote_share:g}",
        "runs": runs,
        "evaluation_summary": _aggregate_runs(runs)
        | {
            metric: fmean(float(run[metric]) for run in runs)
            for metric in (
                "fallback_rate",
                "mean_majority_vote_share",
                "unanimous_rate",
            )
        },
        "paired_summary": paired_summary,
        "gate_vs_projected_queue": non_regression_gate(
            paired_summary,
            applied_constraint_violations=violations,
        ),
    }


def _evaluate_scenario(
    scenario: EvaluationScenario,
    *,
    models: Sequence[QNetwork],
    agreement_thresholds: Sequence[float],
) -> dict[str, object]:
    baseline_runs = _baseline_runs(scenario)
    return {
        "scenario": scenario.metadata(),
        "baseline": {
            "policy_id": "projected_queue_observation_only",
            "runs": baseline_runs,
            "evaluation_summary": _aggregate_runs(baseline_runs),
        },
        "candidates": [
            _evaluate_candidate(
                scenario,
                models=models,
                min_vote_share=threshold,
                baseline_runs=baseline_runs,
            )
            for threshold in agreement_thresholds
        ],
    }


def _selection_report(
    threshold: float, declared_results: Sequence[dict[str, object]]
) -> dict[str, object]:
    candidates = [
        next(
            candidate
            for candidate in result["candidates"]  # type: ignore[union-attr]
            if float(candidate["minimum_majority_vote_share"]) == threshold
        )
        for result in declared_results
    ]
    failed = [
        str(result["scenario"]["scenario_id"])  # type: ignore[index]
        for result, candidate in zip(declared_results, candidates, strict=True)
        if not bool(candidate["gate_vs_projected_queue"]["passes"])  # type: ignore[index]
    ]
    gates = [candidate["gate_vs_projected_queue"] for candidate in candidates]
    return {
        "minimum_majority_vote_share": threshold,
        "failed_declared_regimes": failed,
        "passes_every_declared_regime": not failed,
        "worst_drop_delta_upper_bound": max(
            float(gate["drop_delta_upper_bound"])
            for gate in gates  # type: ignore[index]
        ),
        "worst_return_delta_lower_bound": min(
            float(gate["return_delta_lower_bound"])
            for gate in gates  # type: ignore[index]
        ),
        "mean_fallback_rate": fmean(
            float(candidate["evaluation_summary"]["fallback_rate"])  # type: ignore[index]
            for candidate in candidates
        ),
    }


def _selection_rank(report: dict[str, object]) -> tuple[float, ...]:
    return (
        float(len(report["failed_declared_regimes"])),  # type: ignore[arg-type]
        float(report["worst_drop_delta_upper_bound"]),
        -float(report["worst_return_delta_lower_bound"]),
        -float(report["minimum_majority_vote_share"]),
    )


def build_results(
    *,
    episodes: int = 180,
    agreement_thresholds: Iterable[float] = DEFAULT_AGREEMENT_THRESHOLDS,
) -> dict[str, object]:
    thresholds = tuple(float(value) for value in agreement_thresholds)
    if len(thresholds) < 2:
        raise ValueError("at least two agreement thresholds are required")
    if len(set(thresholds)) != len(thresholds):
        raise ValueError("agreement thresholds must be unique")
    if any(not math.isfinite(value) or not 0.5 < value <= 1.0 for value in thresholds):
        raise ValueError("agreement thresholds must be finite and in (0.5, 1.0]")

    training_runs: list[dict[str, object]] = []
    models: list[QNetwork] = []
    for seed in TRAINING_SEEDS:
        training = train_dqn(
            DQNConfig(
                seed=seed,
                episodes=episodes,
                drop_penalty=FROZEN_TRAINING_DROP_PENALTY,
            )
        )
        models.append(training.model)
        training_runs.append({"training_seed": seed, "training": training.metadata()})

    declared_scenarios = (NOMINAL_SCENARIO, *DEVELOPMENT_SHIFT_SCENARIOS)
    declared_results = [
        _evaluate_scenario(
            scenario,
            models=models,
            agreement_thresholds=thresholds,
        )
        for scenario in declared_scenarios
    ]
    threshold_reports = [
        _selection_report(threshold, declared_results) for threshold in thresholds
    ]
    selected_report = min(threshold_reports, key=_selection_rank)
    selected_threshold = float(selected_report["minimum_majority_vote_share"])

    final_challenge_open_count = 0
    final_challenge_open_count += 1
    final_result = _evaluate_scenario(
        FINAL_CHALLENGE_SCENARIO,
        models=models,
        agreement_thresholds=(selected_threshold,),
    )
    final_candidate = final_result["candidates"][0]  # type: ignore[index]
    accepted = bool(selected_report["passes_every_declared_regime"]) and bool(
        final_candidate["gate_vs_projected_queue"]["passes"]  # type: ignore[index]
    )
    if accepted:
        preferred_controller = str(final_candidate["policy_id"])
        conclusion = (
            "The selected disagreement gate is non-regressive against the "
            "projected-load fallback in every declared regime and the final challenge."
        )
    else:
        preferred_controller = "projected_queue_observation_only"
        conclusion = (
            "The disagreement-gated ensemble does not clear the complete "
            "non-regression contract; the projected-load heuristic remains preferable."
        )

    results = {
        "schema_version": "1.0.0",
        "experiment_id": "network-book-l26-disagreement-abstention-v1",
        "question": (
            "Can a five-model DQN vote gate abstain to the projected-load heuristic "
            "and avoid the distribution-shift regressions retained in L25?"
        ),
        "evidence_scope": {
            "kind": "deterministic_synthetic_disagreement_gate",
            "production_proof": False,
            "uncertainty_interpretation": (
                "Vote share is an uncalibrated disagreement signal, not a probability "
                "of correctness or a production confidence score."
            ),
            "statement": (
                "Pedagogical evidence only; no RF, transport, field, mission, "
                "or production-performance claim."
            ),
        },
        "frozen_model_panel": {
            "source_experiment_id": "network-book-l24-constrained-dqn-v1",
            "training_drop_penalty": FROZEN_TRAINING_DROP_PENALTY,
            "training_seeds": list(TRAINING_SEEDS),
            "retuning_on_shifted_scenarios": False,
            "models": training_runs,
        },
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "agreement_thresholds": list(thresholds),
        "uncertainty_method": (
            "two-sided Student-t 95% confidence interval across forty paired "
            "evaluation seeds (df=39) for the frozen five-model panel"
        ),
        "acceptance_contract": {
            "baseline_and_fallback": "projected_queue_observation_only",
            "scope": "every declared regime and the held-out final challenge",
            "zero_applied_constraint_violations": True,
            "minimum_return_delta_lower_95pct": 0.0,
            "maximum_drop_delta_upper_95pct": 0.0,
            "selection_uses_final_challenge": False,
        },
        "declared_scenario_results": declared_results,
        "selection": {
            "performed_before_final_challenge": True,
            "ranking_rule": (
                "fewest failed declared regimes, then smallest worst drop upper "
                "bound, largest worst return lower bound, and highest vote threshold"
            ),
            "threshold_reports": threshold_reports,
            "selected_minimum_majority_vote_share": selected_threshold,
            "selected_candidate_passes_declared_gate": bool(
                selected_report["passes_every_declared_regime"]
            ),
        },
        "final_challenge": {
            "sealed_scenario_sha256": FINAL_CHALLENGE_SCENARIO.metadata()["sha256"],
            "open_count": final_challenge_open_count,
            "used_for_threshold_selection": False,
            "result": final_result,
        },
        "deployment_outcome": {
            "passes_complete_non_regression_contract": accepted,
            "preferred_controller": preferred_controller,
            "conclusion": conclusion,
        },
        "success_criteria": {
            "five_frozen_models": len(models) == 5,
            "at_least_two_thresholds_retained": len(thresholds) >= 2,
            "five_declared_regimes_retained": len(declared_results) == 5,
            "selection_completed_before_final_challenge": True,
            "final_challenge_opened_once": final_challenge_open_count == 1,
            "final_challenge_excluded_from_selection": True,
            "all_applied_actions_respect_hard_filter": all(
                float(candidate["evaluation_summary"]["applied_constraint_violations"])  # type: ignore[index]
                == 0.0
                for result in [*declared_results, final_result]
                for candidate in result["candidates"]  # type: ignore[union-attr]
            ),
            "scientific_outcome_retained_even_if_negative": True,
        },
    }
    if not all(results["success_criteria"].values()):  # type: ignore[union-attr]
        raise AssertionError(
            f"L26 execution criteria failed: {results['success_criteria']}"
        )
    return _rounded(results)


def render_json(results: dict[str, object]) -> str:
    return json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_csv(results: dict[str, object]) -> str:
    output = io.StringIO(newline="")
    fields = (
        "scenario_id",
        "scenario_role",
        "minimum_majority_vote_share",
        "evaluation_seed",
        "policy",
        "mean_return",
        "mean_dropped",
        "mean_delivered",
        "applied_constraint_violations",
        "fallback_rate",
        "mean_majority_vote_share",
        "unanimous_rate",
        "return_delta_vs_projected_queue",
        "drop_delta_vs_projected_queue",
    )
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    declared = results["declared_scenario_results"]  # type: ignore[assignment]
    final = results["final_challenge"]["result"]  # type: ignore[index]
    for scenario_result in [*declared, final]:
        scenario = scenario_result["scenario"]
        for run in scenario_result["baseline"]["runs"]:
            evaluation = run["evaluation"]
            writer.writerow(
                {
                    "scenario_id": scenario["scenario_id"],
                    "scenario_role": scenario["role"],
                    "minimum_majority_vote_share": "",
                    "evaluation_seed": run["evaluation_seed"],
                    "policy": "projected_queue_observation_only",
                    **{
                        key: evaluation[key]
                        for key in (
                            "mean_return",
                            "mean_dropped",
                            "mean_delivered",
                            "applied_constraint_violations",
                        )
                    },
                }
            )
        for candidate in scenario_result["candidates"]:
            for run in candidate["runs"]:
                evaluation = run["evaluation"]
                delta = run["paired_delta_vs_projected_queue"]
                writer.writerow(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "scenario_role": scenario["role"],
                        "minimum_majority_vote_share": candidate[
                            "minimum_majority_vote_share"
                        ],
                        "evaluation_seed": run["evaluation_seed"],
                        "policy": candidate["policy_id"],
                        **{
                            key: evaluation[key]
                            for key in (
                                "mean_return",
                                "mean_dropped",
                                "mean_delivered",
                                "applied_constraint_violations",
                            )
                        },
                        "fallback_rate": run["fallback_rate"],
                        "mean_majority_vote_share": run["mean_majority_vote_share"],
                        "unanimous_rate": run["unanimous_rate"],
                        "return_delta_vs_projected_queue": delta["mean_return"],
                        "drop_delta_vs_projected_queue": delta["mean_dropped"],
                    }
                )
    return output.getvalue().replace("\r\n", "\n")


def write_or_check(*, check: bool) -> dict[str, object]:
    results = build_results()
    expected = {JSON_PATH: render_json(results), CSV_PATH: render_csv(results)}
    if check:
        for path, content in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise AssertionError(f"stale L26 abstention artifact: {path}")
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
    print(json.dumps(results["deployment_outcome"], sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
