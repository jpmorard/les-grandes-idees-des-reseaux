"""Combined offline integrity gate for the machine-learning laboratories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_environment_lock import write_or_check as check_environment
from build_manifest import write_or_check as check_manifest
from run_benchmarks import JSON_PATH, write_or_check as check_benchmarks
from run_constrained_dqn_experiment import (
    JSON_PATH as L24_JSON_PATH,
    write_or_check as check_l24_experiment,
)
from run_l25_robustness_experiment import (
    JSON_PATH as L25_JSON_PATH,
    write_or_check as check_l25_experiment,
)
from run_l26_abstention_experiment import (
    DEFAULT_AGREEMENT_THRESHOLDS,
    JSON_PATH as L26_JSON_PATH,
    write_or_check as check_l26_experiment,
)
from run_l27_support_guard_experiment import (
    DEFAULT_CALIBRATION_SEEDS,
    DEFAULT_REFERENCE_SEEDS,
    JSON_PATH as L27_JSON_PATH,
    seed_role_contract,
    write_or_check as check_l27_experiment,
)
from verify_notebooks import verify_all


ROOT = Path(__file__).resolve().parent


def validate_result_contract() -> None:
    results = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "benchmark_id",
        "evidence_scope",
        "training_seeds",
        "evaluation_seeds",
        "baselines",
        "dqn_runs",
        "dqn_summary",
        "paired_summary",
        "hard_constraint_probe",
        "rare_classification",
        "success_criteria",
        "negative_findings",
    }
    missing = required - set(results)
    if missing:
        raise AssertionError(f"benchmark result is missing keys: {sorted(missing)}")
    if len(results["training_seeds"]) != 5 or len(results["dqn_runs"]) != 5:
        raise AssertionError("five independent training runs are required")
    if not all(results["success_criteria"].values()):
        raise AssertionError("one or more retained success criteria failed")
    if results["evidence_scope"]["production_proof"] is not False:
        raise AssertionError("synthetic evidence must not claim production proof")


def validate_l24_contract() -> None:
    results = json.loads(L24_JSON_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "experiment_id",
        "evidence_scope",
        "training_seeds",
        "evaluation_seeds",
        "training_drop_penalties",
        "reporting_drop_penalty",
        "objective",
        "acceptance_contract",
        "baselines",
        "candidates",
        "selection",
        "success_criteria",
    }
    missing = required - set(results)
    if missing:
        raise AssertionError(f"L24 result is missing keys: {sorted(missing)}")
    if len(results["training_seeds"]) != 5 or len(results["evaluation_seeds"]) != 40:
        raise AssertionError("L24 requires five training and forty evaluation seeds")
    if len(results["candidates"]) != len(results["training_drop_penalties"]):
        raise AssertionError("L24 must retain one candidate per training penalty")
    if not all(results["success_criteria"].values()):
        raise AssertionError("one or more retained L24 execution criteria failed")
    if results["evidence_scope"]["production_proof"] is not False:
        raise AssertionError("L24 synthetic evidence must not claim production proof")


def validate_l25_contract() -> None:
    results = json.loads(L25_JSON_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "experiment_id",
        "evidence_scope",
        "frozen_candidate",
        "training_seeds",
        "evaluation_seeds",
        "acceptance_contract",
        "training_runs",
        "declared_scenario_results",
        "final_challenge",
        "robustness_outcome",
        "success_criteria",
    }
    missing = required - set(results)
    if missing:
        raise AssertionError(f"L25 result is missing keys: {sorted(missing)}")
    if len(results["training_seeds"]) != 5 or len(results["evaluation_seeds"]) != 40:
        raise AssertionError("L25 requires five training and forty evaluation seeds")
    if len(results["training_runs"]) != 5:
        raise AssertionError("L25 must retain the five frozen training runs")
    if len(results["declared_scenario_results"]) != 5:
        raise AssertionError("L25 must retain the control and four declared shifts")
    if results["final_challenge"]["open_count"] != 1:
        raise AssertionError("L25 final challenge must be opened exactly once")
    if results["frozen_candidate"]["retuning_performed"] is not False:
        raise AssertionError("L25 must not retune the frozen candidate")
    if not all(results["success_criteria"].values()):
        raise AssertionError("one or more retained L25 execution criteria failed")
    if results["evidence_scope"]["production_proof"] is not False:
        raise AssertionError("L25 synthetic evidence must not claim production proof")


def validate_l26_contract() -> None:
    results = json.loads(L26_JSON_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "experiment_id",
        "evidence_scope",
        "frozen_model_panel",
        "evaluation_seeds",
        "agreement_thresholds",
        "acceptance_contract",
        "declared_scenario_results",
        "selection",
        "final_challenge",
        "deployment_outcome",
        "success_criteria",
    }
    missing = required - set(results)
    if missing:
        raise AssertionError(f"L26 result is missing keys: {sorted(missing)}")
    if len(results["frozen_model_panel"]["models"]) != 5:
        raise AssertionError("L26 requires the five-model frozen panel")
    if len(results["evaluation_seeds"]) != 40:
        raise AssertionError("L26 requires forty paired evaluation seeds")
    if results["agreement_thresholds"] != list(DEFAULT_AGREEMENT_THRESHOLDS):
        raise AssertionError("L26 canonical agreement thresholds changed")
    if len(results["declared_scenario_results"]) != 5:
        raise AssertionError("L26 must retain the control and four declared shifts")
    if results["selection"]["performed_before_final_challenge"] is not True:
        raise AssertionError("L26 threshold selection must precede the final challenge")
    if not results["selection"]["ranking_rule"]:
        raise AssertionError("L26 must retain its predeclared threshold ranking rule")
    if results["final_challenge"]["open_count"] != 1:
        raise AssertionError("L26 final challenge must be opened exactly once")
    if results["final_challenge"]["used_for_threshold_selection"] is not False:
        raise AssertionError("L26 final challenge must not select the threshold")
    if not all(results["success_criteria"].values()):
        raise AssertionError("one or more retained L26 execution criteria failed")
    if results["evidence_scope"]["production_proof"] is not False:
        raise AssertionError("L26 synthetic evidence must not claim production proof")


def validate_l27_contract() -> None:
    results = json.loads(L27_JSON_PATH.read_text(encoding="utf-8"))
    models = results["frozen_model_panel"]["models"]
    model_seeds = [model["training"]["config"]["seed"] for model in models]
    if model_seeds != results["frozen_model_panel"]["training_seeds"]:
        raise AssertionError(
            "L27 model seeds must match their recorded training configurations"
        )
    episode_counts = {model["training"]["config"]["episodes"] for model in models}
    if len(episode_counts) != 1:
        raise AssertionError("L27 seed roles require the recorded episodes per model")
    expected_seed_roles = seed_role_contract(
        episodes=episode_counts.pop(),
        reference_seeds=results["monitor_contract"]["reference_seeds"],
        calibration_seeds=results["monitor_contract"]["calibration_seeds"],
        training_seeds=model_seeds,
    )
    if results.get("seed_role_contract") != expected_seed_roles:
        raise AssertionError(
            "L27 seed roles do not match the actual training episode seeds"
        )
    if (
        "monitor_seeds_disjoint_from_training_and_evaluation"
        in results["success_criteria"]
    ):
        raise AssertionError(
            "L27 must not retain the superseded seed-independence claim"
        )
    required = {
        "schema_version",
        "experiment_id",
        "evidence_scope",
        "frozen_model_panel",
        "monitor_contract",
        "evaluation_seeds",
        "acceptance_contract",
        "declared_scenario_results",
        "final_challenge",
        "deployment_outcome",
        "success_criteria",
    }
    missing = required - set(results)
    if missing:
        raise AssertionError(f"L27 result is missing keys: {sorted(missing)}")
    if len(results["frozen_model_panel"]["models"]) != 5:
        raise AssertionError("L27 requires the five-model frozen panel")
    if len(results["evaluation_seeds"]) != 40:
        raise AssertionError("L27 requires forty paired evaluation seeds")
    monitor = results["monitor_contract"]
    if monitor["reference_seeds"] != list(DEFAULT_REFERENCE_SEEDS):
        raise AssertionError("L27 canonical support-reference seeds changed")
    if monitor["calibration_seeds"] != list(DEFAULT_CALIBRATION_SEEDS):
        raise AssertionError("L27 canonical monitor-calibration seeds changed")
    if len(results["declared_scenario_results"]) != 5:
        raise AssertionError("L27 must retain the control and four declared shifts")
    if results["final_challenge"]["open_count"] != 1:
        raise AssertionError("L27 final challenge must be opened exactly once")
    if results["final_challenge"]["used_for_monitor_calibration"] is not False:
        raise AssertionError("L27 final challenge must not calibrate the monitor")
    if not all(results["success_criteria"].values()):
        raise AssertionError("one or more retained L27 execution criteria failed")
    if results["evidence_scope"]["production_proof"] is not False:
        raise AssertionError("L27 synthetic evidence must not claim production proof")


def verify_all_artifacts(*, execute_notebooks: bool) -> None:
    check_environment(check=True)
    check_benchmarks(check=True)
    validate_result_contract()
    check_l24_experiment(check=True)
    validate_l24_contract()
    check_l25_experiment(check=True)
    validate_l25_contract()
    check_l26_experiment(check=True)
    validate_l26_contract()
    check_l27_experiment(check=True)
    validate_l27_contract()
    verify_all(execute=execute_notebooks)
    check_manifest(check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-notebooks", action="store_true")
    args = parser.parse_args()
    verify_all_artifacts(execute_notebooks=args.execute_notebooks)
    print("PASS machine_learning_labs: evidence and artifact integrity verified")


if __name__ == "__main__":
    main()
