from __future__ import annotations

import inspect
import hashlib
import json
from math import isclose
from pathlib import Path

import numpy as np
import pytest
import torch
from gymnasium.utils.env_checker import check_env

from dqn_relay_lab import (
    DQNConfig,
    RelayQueueEnv,
    always_relay_a_policy,
    bellman_targets,
    dqn_policy,
    evaluate_policy,
    filter_action,
    projected_queue_policy,
    random_policy,
    train_dqn,
)
from rare_classification_lab import run_experiment
from return_td_lab import guided_summary, td_error
from run_constrained_dqn_experiment import acceptance_gate
from run_l25_robustness_experiment import (
    FINAL_CHALLENGE_SCENARIO,
    build_results as build_l25_results,
)
from run_l26_abstention_experiment import (
    FINAL_CHALLENGE_SCENARIO as L26_FINAL_CHALLENGE_SCENARIO,
    build_results as build_l26_results,
    non_regression_gate,
)
from run_l27_support_guard_experiment import (
    FINAL_CHALLENGE_SCENARIO as L27_FINAL_CHALLENGE_SCENARIO,
    NominalSupportMonitor,
    build_results as build_l27_results,
    seed_role_contract,
)
from verify_notebooks import verify_all
import verify as evidence_verifier


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "b7fa78258df79f7adfc80f4d5e98c74cf4605948"


def test_return_value_advantage_and_td_chain() -> None:
    summary = guided_summary(0.9)
    assert isclose(summary["q_values"]["A"], -1.79)
    assert isclose(summary["q_values"]["B"], 1.73)
    assert isclose(summary["policy_value"], -0.03)
    assert isclose(summary["advantages"]["A"], -1.76)
    assert isclose(summary["advantages"]["B"], 1.76)
    assert isclose(summary["td_after_a"], -1.3)


def test_termination_and_truncation_bootstrap_differ() -> None:
    terminal = td_error(
        reward=1.0,
        gamma=0.9,
        next_value=3.0,
        current_value=0.5,
        terminated=True,
    )
    truncated = td_error(
        reward=1.0,
        gamma=0.9,
        next_value=3.0,
        current_value=0.5,
        terminated=False,
    )
    assert isclose(terminal, 0.5)
    assert isclose(truncated, 3.2)
    targets = bellman_targets(
        torch.tensor([1.0, 1.0]),
        torch.tensor([3.0, 3.0]),
        torch.tensor([1.0, 0.0]),
        0.9,
    )
    assert torch.allclose(targets, torch.tensor([1.0, 3.7]))


def test_relay_environment_passes_gymnasium_contract() -> None:
    check_env(RelayQueueEnv(horizon=8), skip_render_check=True)


def test_environment_exposes_real_termination_and_time_limit() -> None:
    failed = RelayQueueEnv(
        horizon=8,
        queue_capacity=4,
        drop_termination_threshold=1,
        outage_pattern=(None, None, None, None),
    )
    failed.reset(
        seed=1,
        options={"phase_offset": 2, "queue_a": 4, "queue_b": 0},
    )
    _, _, terminated, truncated, info = failed.step(0)
    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "drop_budget"

    limited = RelayQueueEnv(
        horizon=4,
        drop_termination_threshold=None,
        outage_pattern=(None, None, None, None),
    )
    observation, _ = limited.reset(seed=2)
    for _ in range(4):
        action = projected_queue_policy(observation, np.random.default_rng(2))
        observation, _, terminated, truncated, _ = limited.step(action)
    assert terminated is False
    assert truncated is True


def test_fail_closed_filter_blocks_unavailable_relay() -> None:
    env = RelayQueueEnv(horizon=8)
    observation, _ = env.reset(
        seed=3,
        options={"phase_offset": 1, "queue_a": 0, "queue_b": 0},
    )
    applied, blocked = filter_action(0, observation)
    assert blocked is True
    assert applied == 1
    _, _, _, _, info = env.step(0)
    assert info["applied_action"] == 1
    _, _, _, _, info = env.step(applied)
    assert info["action_allowed"] is True

    metrics = evaluate_policy(
        always_relay_a_policy,
        seeds=range(10, 14),
        drop_termination_threshold=None,
    )
    assert metrics["mean_blocked_proposals"] > 0
    assert metrics["applied_constraint_violations"] == 0


def test_drop_penalty_changes_reward_without_changing_transition() -> None:
    reset_options = {"phase_offset": 2, "queue_a": 10, "queue_b": 0}
    canonical = RelayQueueEnv(
        horizon=8,
        drop_termination_threshold=None,
        drop_penalty=4.0,
        outage_pattern=(None, None, None, None),
    )
    conservative = RelayQueueEnv(
        horizon=8,
        drop_termination_threshold=None,
        drop_penalty=10.0,
        outage_pattern=(None, None, None, None),
    )
    canonical.reset(seed=5, options=reset_options)
    conservative.reset(seed=5, options=reset_options)
    canonical_observation, canonical_reward, _, _, canonical_info = canonical.step(0)
    conservative_observation, conservative_reward, _, _, conservative_info = (
        conservative.step(0)
    )
    assert np.array_equal(canonical_observation, conservative_observation)
    assert canonical_info == conservative_info
    assert canonical_info["dropped"] == 2
    assert isclose(canonical_reward - conservative_reward, 12.0)


def test_shifted_environment_patterns_are_observable_and_validated() -> None:
    env = RelayQueueEnv(
        horizon=8,
        queue_capacity=6,
        arrival_pattern=(1, 5, 1, 5),
        service_a_pattern=(2, 1, 0, 0),
        service_b_pattern=(1, 0, 2, 0),
        outage_pattern=(0, 0, 1, 1),
    )
    observation, _ = env.reset(
        seed=6,
        options={"phase_offset": 1, "queue_a": 0, "queue_b": 0},
    )
    assert np.allclose(observation[2:5], np.asarray((5, 1, 0)) / 6)
    assert observation[5:].tolist() == [0.0, 1.0]

    with pytest.raises(ValueError, match="one entry per traffic phase"):
        RelayQueueEnv(
            arrival_pattern=(1, 2, 3),
            service_a_pattern=(1, 1),
            service_b_pattern=(1, 1, 1),
            outage_pattern=(None, None, None),
        )


def test_l24_acceptance_gate_uses_confidence_bounds() -> None:
    passing = acceptance_gate(
        {
            "mean_return": {"mean": 5.0, "ci95_half_width": 2.0},
            "mean_dropped": {"mean": -4.0, "ci95_half_width": 1.5},
        },
        applied_constraint_violations=0.0,
    )
    assert passing["passes"] is True
    assert passing["return_delta_lower_bound"] == 3.0
    assert passing["drop_delta_upper_bound"] == -2.5

    inconclusive = acceptance_gate(
        {
            "mean_return": {"mean": 5.0, "ci95_half_width": 5.0},
            "mean_dropped": {"mean": -1.0, "ci95_half_width": 2.0},
        },
        applied_constraint_violations=1.0,
    )
    assert inconclusive["passes"] is False
    assert not all(inconclusive["criteria"].values())


def test_l25_smoke_retains_frozen_and_sealed_contracts() -> None:
    results = build_l25_results(episodes=12)
    assert results["frozen_candidate"]["training_drop_penalty"] == 8.0
    assert results["frozen_candidate"]["retuning_performed"] is False
    assert len(results["declared_scenario_results"]) == 5
    assert results["final_challenge"]["open_count"] == 1
    assert results["final_challenge"]["used_for_selection_or_retuning"] is False
    assert (
        results["final_challenge"]["sealed_scenario_sha256"]
        == (FINAL_CHALLENGE_SCENARIO.metadata()["sha256"])
    )
    assert all(results["success_criteria"].values())


def test_l26_non_regression_gate_uses_paired_bounds() -> None:
    passing = non_regression_gate(
        {
            "mean_return": {"mean": 1.5, "ci95_half_width": 1.0},
            "mean_dropped": {"mean": -0.5, "ci95_half_width": 0.25},
        },
        applied_constraint_violations=0.0,
    )
    assert passing["passes"] is True
    assert passing["return_delta_lower_bound"] == 0.5
    assert passing["drop_delta_upper_bound"] == -0.25

    failing = non_regression_gate(
        {
            "mean_return": {"mean": 0.5, "ci95_half_width": 1.0},
            "mean_dropped": {"mean": -0.1, "ci95_half_width": 0.25},
        },
        applied_constraint_violations=1.0,
    )
    assert failing["passes"] is False
    assert not all(failing["criteria"].values())


def test_l26_smoke_selects_before_opening_new_challenge() -> None:
    results = build_l26_results(episodes=12, agreement_thresholds=(0.6, 0.8))
    assert len(results["frozen_model_panel"]["models"]) == 5
    assert len(results["declared_scenario_results"]) == 5
    assert results["selection"]["performed_before_final_challenge"] is True
    assert results["final_challenge"]["open_count"] == 1
    assert results["final_challenge"]["used_for_threshold_selection"] is False
    assert (
        results["final_challenge"]["sealed_scenario_sha256"]
        == L26_FINAL_CHALLENGE_SCENARIO.metadata()["sha256"]
    )
    assert all(results["success_criteria"].values())


def test_l27_nominal_support_monitor_rejects_distant_observation() -> None:
    monitor = NominalSupportMonitor(
        np.asarray(((0.0, 0.0), (1.0, 1.0)), dtype=np.float32),
        threshold=0.2,
    )
    assert monitor.contains(np.asarray((0.1, 0.1), dtype=np.float32)) is True
    assert monitor.contains(np.asarray((0.5, 0.5), dtype=np.float32)) is False
    assert monitor.score(np.asarray((0.5, 0.5), dtype=np.float32)) > 0.2


def test_l27_smoke_calibrates_nominally_before_new_challenge() -> None:
    results = build_l27_results(
        episodes=12,
        reference_seeds=range(100, 104),
        calibration_seeds=range(500, 504),
    )
    assert len(results["frozen_model_panel"]["models"]) == 5
    assert len(results["declared_scenario_results"]) == 5
    assert results["monitor_contract"]["reference_seeds"] == [100, 101, 102, 103]
    assert results["monitor_contract"]["calibration_seeds"] == [500, 501, 502, 503]
    assert results["final_challenge"]["open_count"] == 1
    assert results["final_challenge"]["used_for_monitor_calibration"] is False
    assert (
        results["final_challenge"]["sealed_scenario_sha256"]
        == L27_FINAL_CHALLENGE_SCENARIO.metadata()["sha256"]
    )
    assert all(results["success_criteria"].values())


def test_l27_seed_roles_use_episode_seeds_and_allow_declared_reference_reuse() -> None:
    roles = seed_role_contract(
        episodes=180, reference_seeds=range(100, 140), calibration_seeds=range(500, 540)
    )
    assert roles["training_environment_seeds"] == list(range(7, 239))
    assert roles["reference_training_overlap_seeds"] == list(range(100, 140))
    assert roles["all_monitor_seeds_disjoint_from_training"] is False
    assert roles["reference_training_reuse_allowed"] is True
    with pytest.raises(ValueError, match="calibration seeds"):
        seed_role_contract(episodes=180, reference_seeds=[500], calibration_seeds=[100])
    with pytest.raises(ValueError, match="evaluation seeds"):
        seed_role_contract(
            episodes=1000, reference_seeds=[1500], calibration_seeds=[2000]
        )


def test_l27_correction_preserves_retained_numerical_evidence() -> None:
    result = json.loads((ROOT / "results/l27_support_guard_results.json").read_text())
    correction = json.loads(
        (ROOT / "results/l27_seed_contract_correction.json").read_text()
    )
    fields = correction["unchanged_evidence"]["fields"]
    canonical = json.dumps(
        {field: result[field] for field in fields},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert (
        hashlib.sha256(canonical).hexdigest()
        == correction["unchanged_evidence"]["sha256"]
    )
    assert (
        result["seed_role_contract"]["all_monitor_seeds_disjoint_from_training"]
        is False
    )
    assert (
        "monitor_seeds_disjoint_from_training_and_evaluation"
        not in result["success_criteria"]
    )
    assert (
        result["success_criteria"]["seed_roles_checked_against_training_episode_seeds"]
        is True
    )
    result.pop("seed_role_contract")
    result["success_criteria"].pop("seed_roles_checked_against_training_episode_seeds")
    result["success_criteria"][
        "monitor_seeds_disjoint_from_training_and_evaluation"
    ] = True
    original = (
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    assert (
        hashlib.sha256(original).hexdigest()
        == correction["original_artifact"]["sha256"]
    )


def test_l27_verifier_rejects_a_false_independence_receipt(
    tmp_path, monkeypatch
) -> None:
    result = json.loads((ROOT / "results/l27_support_guard_results.json").read_text())
    result["seed_role_contract"]["all_monitor_seeds_disjoint_from_training"] = True
    path = tmp_path / "false_seed_roles.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    monkeypatch.setattr(evidence_verifier, "L27_JSON_PATH", path)
    with pytest.raises(AssertionError, match="actual training episode seeds"):
        evidence_verifier.validate_l27_contract()


def test_controller_references_share_observation_only_contract() -> None:
    assert len(inspect.signature(random_policy).parameters) == 2
    assert len(inspect.signature(projected_queue_policy).parameters) == 2


def test_dqn_smoke_training_beats_random_on_held_out_seeds() -> None:
    config = DQNConfig(episodes=120, epsilon_decay_steps=3_000)
    training = train_dqn(config)
    seeds = range(2_000, 2_020)
    random_metrics = evaluate_policy(random_policy, seeds=seeds, horizon=config.horizon)
    dqn_metrics = evaluate_policy(
        dqn_policy(training.model), seeds=seeds, horizon=config.horizon
    )
    assert training.losses
    assert dqn_metrics["mean_return"] > random_metrics["mean_return"]
    assert dqn_metrics["mean_dropped"] < random_metrics["mean_dropped"]
    assert dqn_metrics["applied_constraint_violations"] == 0


def test_same_seed_reproduces_model_and_metrics() -> None:
    config = DQNConfig(seed=73, episodes=50, epsilon_decay_steps=1_500)
    first = train_dqn(config)
    second = train_dqn(config)
    for left, right in zip(
        first.model.state_dict().values(),
        second.model.state_dict().values(),
        strict=True,
    ):
        assert torch.equal(left, right)
    assert first.episode_returns == second.episode_returns


def test_rare_classification_uses_sealed_test_contract() -> None:
    result = run_experiment()
    contract = result["split_contract"]
    assert contract["test_open_count"] == 1
    assert len(set(contract["sha256"].values())) == 3
    assert result["selection"]["threshold"] != 0.5
    assert sum(result["final_test"]["counts"].values()) == contract["sizes"]["test"]


def test_notebook_contracts_without_execution() -> None:
    results = verify_all(execute=False)
    assert {result["notebook"] for result in results} == {
        "svd_radio.ipynb",
        "tp_ml_classification_rare.ipynb",
        "tp_rl_dqn_relais.ipynb",
        "tp_rl_retour_q_td.ipynb",
    }


def test_svd_provenance_and_notebook_catalog_are_explicit() -> None:
    sources = (ROOT / "SOURCES.md").read_text(encoding="utf-8")
    catalog = (ROOT / "notebooks" / "README.md").read_text(encoding="utf-8")
    assert SOURCE_COMMIT in sources
    assert "licence MIT" in sources
    assert "ne reprend ni cellule, ni sortie,\nni jeu de données" in sources
    assert SOURCE_COMMIT in catalog
    assert {
        "svd_radio.ipynb",
        "tp_ml_classification_rare.ipynb",
        "tp_rl_dqn_relais.ipynb",
        "tp_rl_retour_q_td.ipynb",
    } <= {name for name in catalog.split("`") if name.endswith(".ipynb")}
