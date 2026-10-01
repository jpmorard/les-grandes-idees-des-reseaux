"""Run the retained L27 nominal-support guard experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
from pathlib import Path
from statistics import fmean
from typing import Iterable, Sequence

import numpy as np

from dqn_relay_lab import (
    DQNConfig,
    Policy,
    QNetwork,
    RelayQueueEnv,
    evaluate_policy,
    filter_action,
    projected_queue_policy,
    random_policy,
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
from run_l26_abstention_experiment import (
    DisagreementGatedPolicy,
    _aggregate_runs,
    _evaluation_seed_summary,
    non_regression_gate,
)


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
JSON_PATH = RESULTS_DIR / "l27_support_guard_results.json"
CSV_PATH = RESULTS_DIR / "l27_support_guard_summary.csv"
DEFAULT_REFERENCE_SEEDS = tuple(range(100, 140))
DEFAULT_CALIBRATION_SEEDS = tuple(range(500, 540))
CALIBRATION_QUANTILE = 0.95


FINAL_CHALLENGE_SCENARIO = EvaluationScenario(
    scenario_id="sealed_support_monitor_challenge",
    role="sealed_final_challenge",
    description=(
        "Unseen combination of shifted bursts, eight-packet queues, crossed service, "
        "and alternating partial outages."
    ),
    queue_capacity=8,
    arrival_pattern=(3, 5, 1, 4),
    service_a_pattern=(1, 0, 2, 0),
    service_b_pattern=(0, 2, 0, 1),
    outage_pattern=(None, 0, None, 1),
)


def _rollout_observations(
    policy: Policy,
    *,
    seed: int,
    scenario: EvaluationScenario = NOMINAL_SCENARIO,
) -> np.ndarray:
    env = RelayQueueEnv(**scenario.environment_kwargs())
    observation, _ = env.reset(seed=seed)
    rng = random.Random(seed)
    observations: list[np.ndarray] = []
    while True:
        observations.append(observation.copy())
        proposed = int(policy(observation, rng))
        action, _ = filter_action(proposed, observation)
        observation, _, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            break
    env.close()
    return np.stack(observations)


def _support_distance(reference: np.ndarray, observation: np.ndarray) -> float:
    array = np.asarray(observation, dtype=np.float32)
    if array.shape != (reference.shape[1],):
        raise ValueError("observation shape does not match the support reference")
    return float(np.linalg.norm(reference - array, axis=1).min())


class NominalSupportMonitor:
    """Nearest-observation support monitor with a fixed distance threshold."""

    def __init__(self, reference: np.ndarray, *, threshold: float) -> None:
        array = np.asarray(reference, dtype=np.float32)
        if array.ndim != 2 or not len(array):
            raise ValueError("reference must be a non-empty two-dimensional array")
        if not np.isfinite(array).all():
            raise ValueError("reference observations must be finite")
        if not math.isfinite(threshold) or threshold < 0.0:
            raise ValueError("threshold must be finite and non-negative")
        self.reference = array
        self.threshold = float(threshold)

    def score(self, observation: np.ndarray) -> float:
        return _support_distance(self.reference, observation)

    def contains(self, observation: np.ndarray) -> bool:
        return self.score(observation) <= self.threshold + 1e-12


class SupportGuardedPolicy:
    """Grant DQN authority only inside nominal support and at unanimity."""

    def __init__(
        self,
        models: Sequence[QNetwork],
        *,
        monitor: NominalSupportMonitor,
        fallback: Policy = projected_queue_policy,
    ) -> None:
        self.ensemble = DisagreementGatedPolicy(
            models,
            min_vote_share=1.0,
            fallback=fallback,
        )
        self.monitor = monitor
        self.fallback = fallback
        self.decisions = 0
        self.support_fallback_decisions = 0
        self.disagreement_fallback_decisions = 0
        self.dqn_authority_decisions = 0
        self.support_score_total = 0.0
        self.maximum_support_score = 0.0

    def __call__(self, observation: np.ndarray, rng: random.Random) -> int:
        score = self.monitor.score(observation)
        self.decisions += 1
        self.support_score_total += score
        self.maximum_support_score = max(self.maximum_support_score, score)
        if score > self.monitor.threshold + 1e-12:
            self.support_fallback_decisions += 1
            return int(self.fallback(observation, rng))

        previous_fallbacks = self.ensemble.fallback_decisions
        action = int(self.ensemble(observation, rng))
        if self.ensemble.fallback_decisions > previous_fallbacks:
            self.disagreement_fallback_decisions += 1
        else:
            self.dqn_authority_decisions += 1
        return action

    def diagnostics(self) -> dict[str, float]:
        if self.decisions == 0:
            raise RuntimeError("the policy has not made a decision")
        return {
            "support_fallback_rate": self.support_fallback_decisions / self.decisions,
            "disagreement_fallback_rate": self.disagreement_fallback_decisions
            / self.decisions,
            "total_fallback_rate": (
                self.support_fallback_decisions + self.disagreement_fallback_decisions
            )
            / self.decisions,
            "dqn_authority_rate": self.dqn_authority_decisions / self.decisions,
            "mean_support_distance": self.support_score_total / self.decisions,
            "maximum_support_distance": self.maximum_support_score,
        }


def _empirical_higher_quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise ValueError("cannot calibrate an empty score sequence")
    if not 0.0 < quantile <= 1.0:
        raise ValueError("quantile must be in (0, 1]")
    ordered = sorted(float(value) for value in values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def build_monitor(
    *,
    reference_seeds: Iterable[int] = DEFAULT_REFERENCE_SEEDS,
    calibration_seeds: Iterable[int] = DEFAULT_CALIBRATION_SEEDS,
) -> tuple[NominalSupportMonitor, dict[str, object]]:
    references = tuple(int(seed) for seed in reference_seeds)
    calibrations = tuple(int(seed) for seed in calibration_seeds)
    if not references or not calibrations:
        raise ValueError("reference and calibration seed sets must be non-empty")
    if set(references) & set(calibrations):
        raise ValueError("reference and calibration seeds must be disjoint")

    policies = (
        ("random_available", random_policy),
        ("projected_queue_observation_only", projected_queue_policy),
    )
    reference_batches: list[np.ndarray] = []
    reference_records: list[dict[str, object]] = []
    for policy_id, policy in policies:
        for seed in references:
            observations = _rollout_observations(policy, seed=seed)
            reference_batches.append(observations)
            reference_records.append(
                {
                    "policy_id": policy_id,
                    "seed": seed,
                    "observation_count": len(observations),
                }
            )
    reference = np.unique(np.vstack(reference_batches), axis=0).astype(np.float32)

    calibration_records: list[dict[str, object]] = []
    episode_maximum_scores: list[float] = []
    for policy_id, policy in policies:
        for seed in calibrations:
            observations = _rollout_observations(policy, seed=seed)
            scores = [_support_distance(reference, item) for item in observations]
            maximum = max(scores)
            episode_maximum_scores.append(maximum)
            calibration_records.append(
                {
                    "policy_id": policy_id,
                    "seed": seed,
                    "observation_count": len(observations),
                    "mean_support_distance": fmean(scores),
                    "maximum_support_distance": maximum,
                }
            )

    threshold = _empirical_higher_quantile(episode_maximum_scores, CALIBRATION_QUANTILE)
    monitor = NominalSupportMonitor(reference, threshold=threshold)
    flagged_episodes = sum(
        float(record["maximum_support_distance"]) > threshold + 1e-12
        for record in calibration_records
    )
    canonical_reference = reference.astype("<f4", copy=False).tobytes()
    metadata = {
        "distance": "nearest Euclidean distance on the normalized observation",
        "reference_scenario": NOMINAL_SCENARIO.metadata(),
        "reference_policies": [policy_id for policy_id, _ in policies],
        "reference_seeds": list(references),
        "reference_trajectory_records": reference_records,
        "reference_observation_count_before_deduplication": sum(
            int(record["observation_count"]) for record in reference_records
        ),
        "unique_reference_observations": len(reference),
        "reference_sha256": hashlib.sha256(canonical_reference).hexdigest(),
        "calibration_scenario": NOMINAL_SCENARIO.metadata(),
        "calibration_policies": [policy_id for policy_id, _ in policies],
        "calibration_seeds": list(calibrations),
        "calibration_episode_records": calibration_records,
        "calibration_quantile": CALIBRATION_QUANTILE,
        "threshold": threshold,
        "calibration_episode_flag_rate": flagged_episodes / len(calibration_records),
    }
    return monitor, metadata


def _paired_summary(
    runs: list[dict[str, object]], field: str
) -> dict[str, dict[str, object]]:
    return {
        metric: _evaluation_seed_summary(
            [float(run[field][metric]) for run in runs]  # type: ignore[index]
        )
        for metric in ("mean_return", "mean_dropped")
    }


def _strict_pareto_benefit(gate: dict[str, object]) -> bool:
    return_lower = float(gate["return_delta_lower_bound"])
    drop_upper = float(gate["drop_delta_upper_bound"])
    return (return_lower > 0.0 and drop_upper <= 0.0) or (
        return_lower >= 0.0 and drop_upper < 0.0
    )


def _evaluate_scenario(
    scenario: EvaluationScenario,
    *,
    models: Sequence[QNetwork],
    monitor: NominalSupportMonitor,
) -> dict[str, object]:
    projected_runs: list[dict[str, object]] = []
    unguarded_runs: list[dict[str, object]] = []
    guarded_runs: list[dict[str, object]] = []
    for seed in EVALUATION_SEEDS:
        projected = evaluate_policy(
            projected_queue_policy,
            seeds=(seed,),
            **scenario.environment_kwargs(),
        )
        unguarded_policy = DisagreementGatedPolicy(models, min_vote_share=1.0)
        unguarded = evaluate_policy(
            unguarded_policy,
            seeds=(seed,),
            **scenario.environment_kwargs(),
        )
        guarded_policy = SupportGuardedPolicy(models, monitor=monitor)
        guarded = evaluate_policy(
            guarded_policy,
            seeds=(seed,),
            **scenario.environment_kwargs(),
        )
        projected_runs.append({"evaluation_seed": seed, "evaluation": projected})
        unguarded_runs.append(
            {
                "evaluation_seed": seed,
                "evaluation": unguarded,
                **unguarded_policy.diagnostics(),
            }
        )
        guarded_runs.append(
            {
                "evaluation_seed": seed,
                "evaluation": guarded,
                **guarded_policy.diagnostics(),
                "paired_delta_vs_projected_queue": {
                    "mean_return": float(guarded["mean_return"])
                    - float(projected["mean_return"]),
                    "mean_dropped": float(guarded["mean_dropped"])
                    - float(projected["mean_dropped"]),
                },
                "paired_delta_vs_unguarded_unanimity": {
                    "mean_return": float(guarded["mean_return"])
                    - float(unguarded["mean_return"]),
                    "mean_dropped": float(guarded["mean_dropped"])
                    - float(unguarded["mean_dropped"]),
                },
            }
        )

    paired_projected = _paired_summary(guarded_runs, "paired_delta_vs_projected_queue")
    paired_unguarded = _paired_summary(
        guarded_runs, "paired_delta_vs_unguarded_unanimity"
    )
    violations = sum(
        float(run["evaluation"]["applied_constraint_violations"])  # type: ignore[index]
        for run in guarded_runs
    )
    gate = non_regression_gate(
        paired_projected,
        applied_constraint_violations=violations,
    )
    return {
        "scenario": scenario.metadata(),
        "projected_queue_baseline": {
            "policy_id": "projected_queue_observation_only",
            "runs": projected_runs,
            "evaluation_summary": _aggregate_runs(projected_runs),
        },
        "unguarded_unanimity": {
            "policy_id": "dqn_ensemble_vote_gate_1",
            "runs": unguarded_runs,
            "evaluation_summary": _aggregate_runs(unguarded_runs)
            | {
                "fallback_rate": fmean(
                    float(run["fallback_rate"]) for run in unguarded_runs
                )
            },
        },
        "support_guarded_unanimity": {
            "policy_id": "nominal_support_then_dqn_unanimity_else_projected_queue",
            "runs": guarded_runs,
            "evaluation_summary": _aggregate_runs(guarded_runs)
            | {
                metric: fmean(float(run[metric]) for run in guarded_runs)
                for metric in (
                    "support_fallback_rate",
                    "disagreement_fallback_rate",
                    "total_fallback_rate",
                    "dqn_authority_rate",
                    "mean_support_distance",
                    "maximum_support_distance",
                )
            },
            "paired_summary": {
                "projected_queue": paired_projected,
                "unguarded_unanimity": paired_unguarded,
            },
            "gate_vs_projected_queue": gate,
            "strict_pareto_benefit": _strict_pareto_benefit(gate),
        },
    }


def seed_role_contract(
    *,
    episodes: int,
    reference_seeds: Iterable[int],
    calibration_seeds: Iterable[int],
    training_seeds: Iterable[int] = TRAINING_SEEDS,
) -> dict[str, object]:
    """Separate model RNG seeds from the environment seeds used each episode.

    The nominal reference may reuse training initial conditions: it constructs
    the support model, not a held-out performance estimate. Calibration and
    evaluation must remain outside all training episode seeds.
    """
    if episodes < 1:
        raise ValueError("episodes must be positive")
    references = set(reference_seeds)
    calibrations = set(calibration_seeds)
    training = {
        seed + episode for seed in training_seeds for episode in range(episodes)
    }
    evaluation = set(EVALUATION_SEEDS)
    if calibrations & (training | references | evaluation):
        raise ValueError(
            "calibration seeds must be disjoint from training episode, reference, "
            "and evaluation seeds"
        )
    if evaluation & (training | references):
        raise ValueError(
            "evaluation seeds must be disjoint from training and reference"
        )
    overlap = sorted(references & training)
    return {
        "training_episode_seed_rule": "model_seed + episode_index",
        "training_episodes_per_model": episodes,
        "training_environment_seeds": sorted(training),
        "reference_training_overlap_seeds": overlap,
        "reference_training_reuse_allowed": True,
        "all_monitor_seeds_disjoint_from_training": not bool(overlap),
        "calibration_disjoint_from_training_reference_and_evaluation": True,
        "evaluation_disjoint_from_training_and_reference": True,
        "interpretation": (
            "Reference trajectories may reuse training initial conditions; only "
            "calibration and evaluation have a held-out seed requirement. Different "
            "seeds do not guarantee distinct observations in this finite simulator."
        ),
    }


def build_results(
    *,
    episodes: int = 180,
    reference_seeds: Iterable[int] = DEFAULT_REFERENCE_SEEDS,
    calibration_seeds: Iterable[int] = DEFAULT_CALIBRATION_SEEDS,
) -> dict[str, object]:
    references = tuple(int(seed) for seed in reference_seeds)
    calibrations = tuple(int(seed) for seed in calibration_seeds)
    seed_roles = seed_role_contract(
        episodes=episodes,
        reference_seeds=references,
        calibration_seeds=calibrations,
    )

    monitor, monitor_metadata = build_monitor(
        reference_seeds=references,
        calibration_seeds=calibrations,
    )
    models: list[QNetwork] = []
    training_runs: list[dict[str, object]] = []
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
        _evaluate_scenario(scenario, models=models, monitor=monitor)
        for scenario in declared_scenarios
    ]

    final_challenge_open_count = 0
    final_challenge_open_count += 1
    final_result = _evaluate_scenario(
        FINAL_CHALLENGE_SCENARIO,
        models=models,
        monitor=monitor,
    )

    declared_non_regression = all(
        bool(
            result["support_guarded_unanimity"]["gate_vs_projected_queue"][  # type: ignore[index]
                "passes"
            ]
        )
        for result in declared_results
    )
    final_non_regression = bool(
        final_result["support_guarded_unanimity"]["gate_vs_projected_queue"][  # type: ignore[index]
            "passes"
        ]
    )
    strict_declared_benefit = any(
        bool(result["support_guarded_unanimity"]["strict_pareto_benefit"])  # type: ignore[index]
        for result in declared_results
    )
    accepted = (
        declared_non_regression and final_non_regression and strict_declared_benefit
    )
    if accepted:
        preferred_controller = "nominal_support_then_dqn_unanimity_else_projected_queue"
        conclusion = (
            "The nominal-support guard clears non-regression in every regime and "
            "retains a strict declared benefit."
        )
    else:
        preferred_controller = "projected_queue_observation_only"
        conclusion = (
            "The nominal-support guard does not clear the complete safety-and-utility "
            "contract; the projected-load heuristic remains preferable."
        )

    results = {
        "schema_version": "1.0.0",
        "experiment_id": "network-book-l27-nominal-support-guard-v1",
        "question": (
            "Can an observation-support monitor plus DQN unanimity avoid the shifted "
            "regressions that model disagreement alone missed in L26?"
        ),
        "evidence_scope": {
            "kind": "deterministic_synthetic_observation_support_guard",
            "production_proof": False,
            "monitor_interpretation": (
                "Nearest-observation distance is a synthetic support diagnostic, not "
                "a calibrated probability of correctness or operational OOD proof."
            ),
            "statement": (
                "Pedagogical evidence only; no RF, transport, field, mission, "
                "or production-performance claim."
            ),
        },
        "frozen_model_panel": {
            "source_experiment_id": "network-book-l26-disagreement-abstention-v1",
            "training_drop_penalty": FROZEN_TRAINING_DROP_PENALTY,
            "training_seeds": list(TRAINING_SEEDS),
            "retuning_on_shifted_scenarios": False,
            "models": training_runs,
        },
        "monitor_contract": monitor_metadata,
        "seed_role_contract": seed_roles,
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "acceptance_contract": {
            "baseline_and_fallback": "projected_queue_observation_only",
            "scope": "every declared regime and the held-out final challenge",
            "zero_applied_constraint_violations": True,
            "minimum_return_delta_lower_95pct": 0.0,
            "maximum_drop_delta_upper_95pct": 0.0,
            "strict_pareto_benefit_in_at_least_one_declared_regime": True,
            "monitor_calibration_uses_shifted_or_final_scenarios": False,
        },
        "declared_scenario_results": declared_results,
        "final_challenge": {
            "sealed_scenario_sha256": FINAL_CHALLENGE_SCENARIO.metadata()["sha256"],
            "open_count": final_challenge_open_count,
            "used_for_monitor_calibration": False,
            "result": final_result,
        },
        "deployment_outcome": {
            "passes_all_declared_non_regression_gates": declared_non_regression,
            "passes_final_non_regression_gate": final_non_regression,
            "has_strict_declared_pareto_benefit": strict_declared_benefit,
            "passes_complete_safety_and_utility_contract": accepted,
            "preferred_controller": preferred_controller,
            "conclusion": conclusion,
        },
        "success_criteria": {
            "five_frozen_models": len(models) == 5,
            "reference_and_calibration_seeds_disjoint": not (
                set(references) & set(calibrations)
            ),
            "seed_roles_checked_against_training_episode_seeds": True,
            "monitor_calibrated_on_nominal_scenario_only": True,
            "five_declared_regimes_retained": len(declared_results) == 5,
            "final_challenge_opened_once": final_challenge_open_count == 1,
            "final_challenge_excluded_from_monitor_calibration": True,
            "all_applied_actions_respect_hard_filter": all(
                float(
                    result["support_guarded_unanimity"]["evaluation_summary"][  # type: ignore[index]
                        "applied_constraint_violations"
                    ]
                )
                == 0.0
                for result in [*declared_results, final_result]
            ),
            "scientific_outcome_retained_even_if_negative": True,
        },
    }
    if not all(results["success_criteria"].values()):  # type: ignore[union-attr]
        raise AssertionError(
            f"L27 execution criteria failed: {results['success_criteria']}"
        )
    return _rounded(results)


def render_json(results: dict[str, object]) -> str:
    return json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_csv(results: dict[str, object]) -> str:
    output = io.StringIO(newline="")
    fields = (
        "scenario_id",
        "scenario_role",
        "evaluation_seed",
        "policy",
        "mean_return",
        "mean_dropped",
        "mean_delivered",
        "applied_constraint_violations",
        "support_fallback_rate",
        "disagreement_fallback_rate",
        "total_fallback_rate",
        "dqn_authority_rate",
        "mean_support_distance",
        "maximum_support_distance",
        "return_delta_vs_projected_queue",
        "drop_delta_vs_projected_queue",
        "return_delta_vs_unguarded_unanimity",
        "drop_delta_vs_unguarded_unanimity",
    )
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    declared = results["declared_scenario_results"]  # type: ignore[assignment]
    final = results["final_challenge"]["result"]  # type: ignore[index]
    for scenario_result in [*declared, final]:
        scenario = scenario_result["scenario"]
        for key in ("projected_queue_baseline", "unguarded_unanimity"):
            controller = scenario_result[key]
            for run in controller["runs"]:
                evaluation = run["evaluation"]
                writer.writerow(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "scenario_role": scenario["role"],
                        "evaluation_seed": run["evaluation_seed"],
                        "policy": controller["policy_id"],
                        **{
                            metric: evaluation[metric]
                            for metric in (
                                "mean_return",
                                "mean_dropped",
                                "mean_delivered",
                                "applied_constraint_violations",
                            )
                        },
                    }
                )
        controller = scenario_result["support_guarded_unanimity"]
        for run in controller["runs"]:
            evaluation = run["evaluation"]
            projected_delta = run["paired_delta_vs_projected_queue"]
            unguarded_delta = run["paired_delta_vs_unguarded_unanimity"]
            writer.writerow(
                {
                    "scenario_id": scenario["scenario_id"],
                    "scenario_role": scenario["role"],
                    "evaluation_seed": run["evaluation_seed"],
                    "policy": controller["policy_id"],
                    **{
                        metric: evaluation[metric]
                        for metric in (
                            "mean_return",
                            "mean_dropped",
                            "mean_delivered",
                            "applied_constraint_violations",
                        )
                    },
                    **{
                        metric: run[metric]
                        for metric in (
                            "support_fallback_rate",
                            "disagreement_fallback_rate",
                            "total_fallback_rate",
                            "dqn_authority_rate",
                            "mean_support_distance",
                            "maximum_support_distance",
                        )
                    },
                    "return_delta_vs_projected_queue": projected_delta["mean_return"],
                    "drop_delta_vs_projected_queue": projected_delta["mean_dropped"],
                    "return_delta_vs_unguarded_unanimity": unguarded_delta[
                        "mean_return"
                    ],
                    "drop_delta_vs_unguarded_unanimity": unguarded_delta[
                        "mean_dropped"
                    ],
                }
            )
    return output.getvalue().replace("\r\n", "\n")


def write_or_check(*, check: bool) -> dict[str, object]:
    results = build_results()
    expected = {JSON_PATH: render_json(results), CSV_PATH: render_csv(results)}
    if check:
        for path, content in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise AssertionError(f"stale L27 support-guard artifact: {path}")
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
    monitor = results["monitor_contract"]  # type: ignore[assignment]
    print(
        json.dumps(
            {
                "unique_reference_observations": monitor[
                    "unique_reference_observations"
                ],
                "threshold": monitor["threshold"],
                "calibration_episode_flag_rate": monitor[
                    "calibration_episode_flag_rate"
                ],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    print(json.dumps(results["deployment_outcome"], sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
