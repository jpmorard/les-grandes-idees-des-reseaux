"""Small, dependency-free calculations for the return/Q/TD laboratory."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite


REWARD_TRAJECTORIES: dict[str, tuple[float, ...]] = {
    "A": (1.0, 0.5, -4.0),
    "B": (0.2, 0.8, 1.0),
}


def _finite_number(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def validate_gamma(gamma: float) -> float:
    """Return a finite discount factor in the closed interval [0, 1]."""

    checked = _finite_number(gamma, "gamma")
    if not 0.0 <= checked <= 1.0:
        raise ValueError("gamma must be between 0 and 1")
    return checked


def discounted_return(rewards: Sequence[float], gamma: float) -> float:
    """Compute G_t = sum_k gamma**k r_(t+k+1)."""

    checked_gamma = validate_gamma(gamma)
    return sum(
        checked_gamma**offset * _finite_number(reward, "reward")
        for offset, reward in enumerate(rewards)
    )


def action_values(
    reward_trajectories: Mapping[str, Sequence[float]], gamma: float
) -> dict[str, float]:
    """Compute deterministic action values for the supplied trajectories."""

    if not reward_trajectories:
        raise ValueError("at least one action is required")
    return {
        str(action): discounted_return(rewards, gamma)
        for action, rewards in reward_trajectories.items()
    }


def policy_value(
    q_values: Mapping[str, float], action_probabilities: Mapping[str, float]
) -> float:
    """Compute V^pi(s) from Q^pi(s,a) and a discrete policy."""

    if set(q_values) != set(action_probabilities):
        raise ValueError("q_values and action_probabilities must share their actions")
    probabilities = {
        action: _finite_number(probability, "probability")
        for action, probability in action_probabilities.items()
    }
    if any(probability < 0.0 for probability in probabilities.values()):
        raise ValueError("action probabilities must be non-negative")
    if abs(sum(probabilities.values()) - 1.0) > 1e-9:
        raise ValueError("action probabilities must sum to one")
    return sum(
        probabilities[action] * _finite_number(q_values[action], "q_value")
        for action in q_values
    )


def advantages(q_values: Mapping[str, float], value: float) -> dict[str, float]:
    """Compute A^pi(s,a) = Q^pi(s,a) - V^pi(s)."""

    checked_value = _finite_number(value, "value")
    return {
        action: _finite_number(q_value, "q_value") - checked_value
        for action, q_value in q_values.items()
    }


def td_error(
    *,
    reward: float,
    gamma: float,
    next_value: float,
    current_value: float,
    terminated: bool,
) -> float:
    """Compute a one-step TD error with correct termination bootstrapping.

    A truncation is represented by ``terminated=False``: the next value is then
    bootstrapped because the modeled world did not reach a natural terminal
    state.
    """

    bootstrap = 0.0 if terminated else validate_gamma(gamma) * _finite_number(
        next_value, "next_value"
    )
    return (
        _finite_number(reward, "reward")
        + bootstrap
        - _finite_number(current_value, "current_value")
    )


def guided_summary(gamma: float = 0.9) -> dict[str, object]:
    """Return the complete numerical chain used by TP L20."""

    q_values = action_values(REWARD_TRAJECTORIES, gamma)
    value = policy_value(q_values, {"A": 0.5, "B": 0.5})
    return {
        "gamma": validate_gamma(gamma),
        "q_values": q_values,
        "policy_value": value,
        "advantages": advantages(q_values, value),
        "td_after_a": td_error(
            reward=1.0,
            gamma=gamma,
            next_value=-2.0,
            current_value=0.5,
            terminated=False,
        ),
    }


if __name__ == "__main__":
    summary = guided_summary()
    assert abs(summary["q_values"]["A"] - (-1.79)) < 1e-9
    assert abs(summary["q_values"]["B"] - 1.73) < 1e-9
    assert abs(summary["td_after_a"] - (-1.3)) < 1e-9
    print(summary)
