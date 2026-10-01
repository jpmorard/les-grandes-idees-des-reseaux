"""Run the retained L25 distribution-shift robustness experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

from dqn_relay_lab import (
    ARRIVAL_PATTERN,
    DEFAULT_OUTAGE_PATTERN,
    SERVICE_A_PATTERN,
    SERVICE_B_PATTERN,
    DQNConfig,
    dqn_policy,
    evaluate_policy,
    projected_queue_policy,
    random_policy,
    train_dqn,
)
from run_benchmarks import EVALUATION_SEEDS, TRAINING_SEEDS
from run_constrained_dqn_experiment import (
    REPORTING_DROP_PENALTY,
    _rounded,
    _summary,
    acceptance_gate,
)


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
JSON_PATH = RESULTS_DIR / "l25_robustness_results.json"
CSV_PATH = RESULTS_DIR / "l25_robustness_summary.csv"
FROZEN_TRAINING_DROP_PENALTY = 8.0


@dataclass(frozen=True)
class EvaluationScenario:
    scenario_id: str
    role: str
    description: str
    queue_capacity: int = 10
    horizon: int = 48
    drop_termination_threshold: int | None = 20
    arrival_pattern: tuple[int, ...] = ARRIVAL_PATTERN
    service_a_pattern: tuple[int, ...] = SERVICE_A_PATTERN
    service_b_pattern: tuple[int, ...] = SERVICE_B_PATTERN
    outage_pattern: tuple[int | None, ...] = DEFAULT_OUTAGE_PATTERN

    def environment_kwargs(self) -> dict[str, object]:
        return {
            "queue_capacity": self.queue_capacity,
            "horizon": self.horizon,
            "drop_termination_threshold": self.drop_termination_threshold,
            "drop_penalty": REPORTING_DROP_PENALTY,
            "arrival_pattern": self.arrival_pattern,
            "service_a_pattern": self.service_a_pattern,
            "service_b_pattern": self.service_b_pattern,
            "outage_pattern": self.outage_pattern,
        }

    def metadata(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "scenario_id": self.scenario_id,
            "role": self.role,
            "description": self.description,
            **self.environment_kwargs(),
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        payload["sha256"] = hashlib.sha256(canonical).hexdigest()
        return payload


NOMINAL_SCENARIO = EvaluationScenario(
    scenario_id="nominal_control",
    role="control",
    description="Canonical L24 traffic, service, capacity, and outage pattern.",
)
DEVELOPMENT_SHIFT_SCENARIOS = (
    EvaluationScenario(
        scenario_id="bursty_arrivals",
        role="declared_shift",
        description="Same mean demand as nominal, concentrated into alternating bursts.",
        arrival_pattern=(1, 4, 1, 4),
    ),
    EvaluationScenario(
        scenario_id="extended_outages",
        role="declared_shift",
        description="Each relay is unavailable for two consecutive traffic phases.",
        outage_pattern=(0, 0, 1, 1),
    ),
    EvaluationScenario(
        scenario_id="reduced_capacity",
        role="declared_shift",
        description="Both relay queues are reduced from ten to six packets.",
        queue_capacity=6,
    ),
    EvaluationScenario(
        scenario_id="shifted_service_asymmetry",
        role="declared_shift",
        description="Service opportunities move across relays and traffic phases.",
        service_a_pattern=(3, 0, 0, 0),
        service_b_pattern=(0, 1, 2, 1),
    ),
)
FINAL_CHALLENGE_SCENARIO = EvaluationScenario(
    scenario_id="sealed_composite_challenge",
    role="sealed_final_challenge",
    description=(
        "Unseen composite of burstier arrivals, smaller queues, shifted outages, "
        "and shifted service."
    ),
    queue_capacity=6,
    arrival_pattern=(1, 5, 1, 5),
    service_a_pattern=(2, 1, 0, 0),
    service_b_pattern=(1, 0, 2, 0),
    outage_pattern=(0, None, 1, None),
)


def _paired_summaries(
    runs: list[dict[str, object]], field: str
) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    for metric in ("mean_return", "mean_dropped"):
        values = [float(run[field][metric]) for run in runs]  # type: ignore[index]
        summaries[metric] = _summary(values)
    return summaries


def _evaluate_scenario(
    scenario: EvaluationScenario,
    *,
    trained_models: dict[int, object],
) -> dict[str, object]:
    environment_kwargs = scenario.environment_kwargs()
    baseline_random = evaluate_policy(
        random_policy,
        seeds=EVALUATION_SEEDS,
        **environment_kwargs,
    )
    baseline_projected = evaluate_policy(
        projected_queue_policy,
        seeds=EVALUATION_SEEDS,
        **environment_kwargs,
    )
    runs: list[dict[str, object]] = []
    for seed in TRAINING_SEEDS:
        evaluation = evaluate_policy(
            dqn_policy(trained_models[seed]),  # type: ignore[arg-type]
            seeds=EVALUATION_SEEDS,
            **environment_kwargs,
        )
        runs.append(
            {
                "training_seed": seed,
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
    paired_random = _paired_summaries(runs, "paired_delta_vs_random")
    paired_projected = _paired_summaries(runs, "paired_delta_vs_projected_queue")
    applied_violations = sum(
        float(run["evaluation"]["applied_constraint_violations"])  # type: ignore[index]
        for run in runs
    )
    return {
        "scenario": scenario.metadata(),
        "baselines": {
            "random_available": baseline_random,
            "projected_queue_observation_only": baseline_projected,
        },
        "dqn_runs": runs,
        "paired_summary": {
            "random": paired_random,
            "projected_queue": paired_projected,
        },
        "gate_vs_random": acceptance_gate(
            paired_random,
            applied_constraint_violations=applied_violations,
        ),
        "gate_vs_projected_queue": acceptance_gate(
            paired_projected,
            applied_constraint_violations=applied_violations,
            baseline="projected_queue_observation_only",
        ),
    }


def build_results(*, episodes: int = 180) -> dict[str, object]:
    trained_models: dict[int, object] = {}
    training_runs: list[dict[str, object]] = []
    for seed in TRAINING_SEEDS:
        config = DQNConfig(
            seed=seed,
            episodes=episodes,
            drop_penalty=FROZEN_TRAINING_DROP_PENALTY,
        )
        training = train_dqn(config)
        trained_models[seed] = training.model
        training_runs.append(
            {
                "training_seed": seed,
                "training": training.metadata(),
            }
        )

    declared_scenarios = (NOMINAL_SCENARIO, *DEVELOPMENT_SHIFT_SCENARIOS)
    scenario_results = [
        _evaluate_scenario(scenario, trained_models=trained_models)
        for scenario in declared_scenarios
    ]

    final_challenge_open_count = 0
    final_challenge_open_count += 1
    final_challenge = _evaluate_scenario(
        FINAL_CHALLENGE_SCENARIO, trained_models=trained_models
    )
    all_results = [*scenario_results, final_challenge]
    accepted_scenarios = [
        str(result["scenario"]["scenario_id"])  # type: ignore[index]
        for result in all_results
        if bool(result["gate_vs_projected_queue"]["passes"])  # type: ignore[index]
    ]
    failed_scenarios = [
        str(result["scenario"]["scenario_id"])  # type: ignore[index]
        for result in all_results
        if not bool(result["gate_vs_projected_queue"]["passes"])  # type: ignore[index]
    ]
    robustness_passes = not failed_scenarios
    if robustness_passes:
        preferred_controller = "dqn_training_drop_penalty_8"
        conclusion = (
            "The frozen DQN passes the predeclared worst-case gate against the "
            "projected-load heuristic in every retained regime."
        )
    else:
        preferred_controller = "projected_queue_observation_only"
        conclusion = (
            "The frozen DQN does not pass the predeclared worst-case gate against "
            "the projected-load heuristic; the simpler heuristic remains preferable."
        )

    results = {
        "schema_version": "1.0.0",
        "experiment_id": "network-book-l25-distribution-shift-v1",
        "question": (
            "Does the frozen L24 penalty-8 DQN robustly outperform the "
            "projected-load heuristic under unseen operating shifts?"
        ),
        "evidence_scope": {
            "kind": "deterministic_synthetic_distribution_shift",
            "production_proof": False,
            "statement": (
                "Pedagogical evidence only; no RF, transport, field, mission, "
                "or production-performance claim."
            ),
        },
        "frozen_candidate": {
            "source_experiment_id": "network-book-l24-constrained-dqn-v1",
            "training_drop_penalty": FROZEN_TRAINING_DROP_PENALTY,
            "retuning_performed": False,
            "training_environment": "nominal_control",
        },
        "training_seeds": list(TRAINING_SEEDS),
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "uncertainty_method": (
            "two-sided Student-t 95% confidence interval across five independent "
            "training seeds (df=4); forty held-out scenarios are paired per regime"
        ),
        "acceptance_contract": {
            "baseline": "projected_queue_observation_only",
            "scope": "every retained regime including the sealed final challenge",
            "zero_applied_constraint_violations": True,
            "maximum_drop_delta_upper_95pct": 0.0,
            "minimum_return_delta_lower_95pct_exclusive": 0.0,
        },
        "training_runs": training_runs,
        "declared_scenario_results": scenario_results,
        "final_challenge": {
            "sealed_scenario_sha256": FINAL_CHALLENGE_SCENARIO.metadata()["sha256"],
            "open_count": final_challenge_open_count,
            "used_for_selection_or_retuning": False,
            "result": final_challenge,
        },
        "robustness_outcome": {
            "accepted_scenarios": accepted_scenarios,
            "failed_scenarios": failed_scenarios,
            "passes_worst_case_gate": robustness_passes,
            "preferred_controller": preferred_controller,
            "conclusion": conclusion,
        },
        "success_criteria": {
            "five_frozen_training_runs": len(training_runs) == 5,
            "forty_paired_evaluation_seeds_per_regime": all(
                all(
                    float(run["evaluation"]["episodes"]) == 40.0  # type: ignore[index]
                    for run in result["dqn_runs"]  # type: ignore[union-attr]
                )
                for result in all_results
            ),
            "four_declared_shifts_retained": len(DEVELOPMENT_SHIFT_SCENARIOS) == 4,
            "final_challenge_opened_once": final_challenge_open_count == 1,
            "no_retuning_on_shifted_scenarios": True,
            "all_candidates_respect_hard_filter": all(
                bool(
                    result["gate_vs_projected_queue"]["criteria"][  # type: ignore[index]
                        "zero_applied_constraint_violations"
                    ]
                )
                for result in all_results
            ),
            "scientific_outcome_retained_even_if_negative": True,
        },
    }
    if not all(results["success_criteria"].values()):  # type: ignore[union-attr]
        raise AssertionError(
            f"L25 execution criteria failed: {results['success_criteria']}"
        )
    return _rounded(results)


def render_json(results: dict[str, object]) -> str:
    return json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_csv(results: dict[str, object]) -> str:
    output = io.StringIO(newline="")
    fields = (
        "scenario_id",
        "scenario_role",
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
    declared = results["declared_scenario_results"]  # type: ignore[assignment]
    final = results["final_challenge"]["result"]  # type: ignore[index]
    for result in [*declared, final]:
        scenario = result["scenario"]
        for name, metrics in result["baselines"].items():
            writer.writerow(
                {
                    "scenario_id": scenario["scenario_id"],
                    "scenario_role": scenario["role"],
                    "training_seed": "",
                    "policy": name,
                    **{
                        key: metrics[key]
                        for key in (
                            "mean_return",
                            "mean_dropped",
                            "mean_delivered",
                            "applied_constraint_violations",
                        )
                    },
                }
            )
        for run in result["dqn_runs"]:
            evaluation = run["evaluation"]
            versus_random = run["paired_delta_vs_random"]
            versus_projected = run["paired_delta_vs_projected_queue"]
            writer.writerow(
                {
                    "scenario_id": scenario["scenario_id"],
                    "scenario_role": scenario["role"],
                    "training_seed": run["training_seed"],
                    "policy": "dqn_training_drop_penalty_8",
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
                raise AssertionError(f"stale L25 robustness artifact: {path}")
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
    print(json.dumps(results["robustness_outcome"], sort_keys=True))


if __name__ == "__main__":
    main()
