"""Auditable DQN laboratory for a constrained two-relay queue.

The environment is deliberately small and synthetic. It demonstrates an
observation-only controller contract, a fail-closed action filter, and the
difference between a natural terminal condition and a time-limit truncation.
It is not RF, transport, mission, or production-network validation.

The remaining drop budget is hidden from every controller, so the published
observation is partially observable; the memoryless DQN is an approximation.
The horizon is an external collection limit, not an intrinsic finite-horizon
terminal condition. Its truncation therefore preserves bootstrapping.
"""

from __future__ import annotations

import math
import random
from collections import deque
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from statistics import fmean, pstdev
from typing import Any

import gymnasium as gym
import numpy as np
import torch
from gymnasium import spaces
from torch import nn


ARRIVAL_PATTERN = (2, 3, 2, 3)
SERVICE_A_PATTERN = (2, 2, 0, 0)
SERVICE_B_PATTERN = (1, 1, 1, 1)
DEFAULT_OUTAGE_PATTERN: tuple[int | None, ...] = (None, 0, None, 1)

QUEUE_A = 0
QUEUE_B = 1
ARRIVAL = 2
SERVICE_A = 3
SERVICE_B = 4
AVAILABLE_A = 5
AVAILABLE_B = 6
OBSERVATION_SIZE = 7


def _validate_outage_pattern(
    pattern: Sequence[int | None],
    *,
    phase_count: int,
) -> tuple[int | None, ...]:
    checked = tuple(pattern)
    if len(checked) != phase_count:
        raise ValueError("outage_pattern must have one entry per traffic phase")
    if any(value not in (None, 0, 1) for value in checked):
        raise ValueError("an outage entry must be None, relay 0, or relay 1")
    return checked


def _validate_traffic_pattern(
    name: str,
    pattern: Sequence[int],
    *,
    queue_capacity: int,
    phase_count: int | None = None,
) -> tuple[int, ...]:
    checked = tuple(pattern)
    if not checked:
        raise ValueError(f"{name} must contain at least one traffic phase")
    if phase_count is not None and len(checked) != phase_count:
        raise ValueError(f"{name} must have one entry per traffic phase")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= queue_capacity
        for value in checked
    ):
        raise ValueError(
            f"{name} entries must be integers between zero and queue_capacity"
        )
    return checked


def action_mask_from_observation(observation: np.ndarray) -> np.ndarray:
    """Return the two allowed-action flags carried by the observation."""

    array = np.asarray(observation, dtype=np.float32)
    if array.shape != (OBSERVATION_SIZE,):
        raise ValueError(f"observation must have shape ({OBSERVATION_SIZE},)")
    mask = array[[AVAILABLE_A, AVAILABLE_B]] >= 0.5
    if not bool(mask.any()):
        raise RuntimeError("the observation exposes no authorized relay")
    return mask


def projected_queue_loads(observation: np.ndarray) -> np.ndarray:
    """Project normalized queue load using only observable quantities."""

    array = np.asarray(observation, dtype=np.float32)
    return np.asarray(
        (
            max(0.0, float(array[QUEUE_A] + array[ARRIVAL] - array[SERVICE_A])),
            max(0.0, float(array[QUEUE_B] + array[ARRIVAL] - array[SERVICE_B])),
        ),
        dtype=np.float32,
    )


def filter_action(proposed_action: int, observation: np.ndarray) -> tuple[int, bool]:
    """Apply a fail-closed mask and return ``(applied_action, blocked)``."""

    if proposed_action not in (0, 1):
        raise ValueError(f"invalid proposed action: {proposed_action!r}")
    mask = action_mask_from_observation(observation)
    if bool(mask[proposed_action]):
        return proposed_action, False
    projected = projected_queue_loads(observation)
    candidates = [action for action in (0, 1) if bool(mask[action])]
    fallback = min(candidates, key=lambda action: (float(projected[action]), action))
    return fallback, True


class RelayQueueEnv(gym.Env[np.ndarray, int]):
    """Route one synthetic batch toward an authorized relay at every step."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        horizon: int = 48,
        queue_capacity: int = 10,
        drop_termination_threshold: int | None = 20,
        drop_penalty: float = 4.0,
        arrival_pattern: Sequence[int] = ARRIVAL_PATTERN,
        service_a_pattern: Sequence[int] = SERVICE_A_PATTERN,
        service_b_pattern: Sequence[int] = SERVICE_B_PATTERN,
        outage_pattern: Sequence[int | None] = DEFAULT_OUTAGE_PATTERN,
    ) -> None:
        super().__init__()
        if horizon < 4:
            raise ValueError("horizon must be at least four steps")
        if queue_capacity < 4:
            raise ValueError("queue_capacity must be at least four packets")
        if drop_termination_threshold is not None and drop_termination_threshold < 1:
            raise ValueError("drop_termination_threshold must be positive or None")
        if not math.isfinite(drop_penalty) or drop_penalty < 0.0:
            raise ValueError("drop_penalty must be finite and non-negative")
        checked_arrivals = _validate_traffic_pattern(
            "arrival_pattern", arrival_pattern, queue_capacity=queue_capacity
        )
        phase_count = len(checked_arrivals)
        checked_service_a = _validate_traffic_pattern(
            "service_a_pattern",
            service_a_pattern,
            queue_capacity=queue_capacity,
            phase_count=phase_count,
        )
        checked_service_b = _validate_traffic_pattern(
            "service_b_pattern",
            service_b_pattern,
            queue_capacity=queue_capacity,
            phase_count=phase_count,
        )
        self.horizon = int(horizon)
        self.queue_capacity = int(queue_capacity)
        self.drop_termination_threshold = drop_termination_threshold
        self.drop_penalty = float(drop_penalty)
        self.arrival_pattern = checked_arrivals
        self.service_a_pattern = checked_service_a
        self.service_b_pattern = checked_service_b
        self.outage_pattern = _validate_outage_pattern(
            outage_pattern, phase_count=phase_count
        )
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(
            low=np.zeros(OBSERVATION_SIZE, dtype=np.float32),
            high=np.ones(OBSERVATION_SIZE, dtype=np.float32),
            dtype=np.float32,
        )
        self.step_index = 0
        self.phase_offset = 0
        self.queue_a = 0
        self.queue_b = 0
        self.total_dropped = 0
        self.total_delivered = 0

    def _phase(self) -> int:
        return (self.step_index + self.phase_offset) % len(self.arrival_pattern)

    def action_mask(self) -> np.ndarray:
        unavailable = self.outage_pattern[self._phase()]
        return np.asarray((unavailable != 0, unavailable != 1), dtype=np.bool_)

    def _observation(self) -> np.ndarray:
        phase = self._phase()
        mask = self.action_mask()
        return np.asarray(
            (
                self.queue_a / self.queue_capacity,
                self.queue_b / self.queue_capacity,
                self.arrival_pattern[phase] / self.queue_capacity,
                self.service_a_pattern[phase] / self.queue_capacity,
                self.service_b_pattern[phase] / self.queue_capacity,
                float(mask[0]),
                float(mask[1]),
            ),
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        options = options or {}
        unknown = set(options) - {"phase_offset", "queue_a", "queue_b"}
        if unknown:
            raise ValueError(f"unknown reset options: {sorted(unknown)}")
        self.step_index = 0
        self.phase_offset = int(
            options.get(
                "phase_offset", self.np_random.integers(0, len(self.arrival_pattern))
            )
        )
        self.queue_a = int(options.get("queue_a", self.np_random.integers(0, 3)))
        self.queue_b = int(options.get("queue_b", self.np_random.integers(0, 3)))
        if not 0 <= self.phase_offset < len(self.arrival_pattern):
            raise ValueError("phase_offset is outside the traffic pattern")
        if not 0 <= self.queue_a <= self.queue_capacity:
            raise ValueError("queue_a is outside the queue capacity")
        if not 0 <= self.queue_b <= self.queue_capacity:
            raise ValueError("queue_b is outside the queue capacity")
        self.total_dropped = 0
        self.total_delivered = 0
        observation = self._observation()
        return observation, {
            "phase": self._phase(),
            "action_mask": self.action_mask().tolist(),
        }

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action!r}")
        mask = self.action_mask()
        if not bool(mask[int(action)]):
            action = int(np.flatnonzero(self.action_mask())[0])

        phase = self._phase()
        arrival = self.arrival_pattern[phase]
        if int(action) == 0:
            self.queue_a += arrival
        else:
            self.queue_b += arrival

        dropped = max(0, self.queue_a - self.queue_capacity) + max(
            0, self.queue_b - self.queue_capacity
        )
        self.queue_a = min(self.queue_a, self.queue_capacity)
        self.queue_b = min(self.queue_b, self.queue_capacity)

        delivered_a = min(self.queue_a, self.service_a_pattern[phase])
        delivered_b = min(self.queue_b, self.service_b_pattern[phase])
        self.queue_a -= delivered_a
        self.queue_b -= delivered_b
        delivered = delivered_a + delivered_b

        queue_cost = 0.18 * (self.queue_a + self.queue_b)
        reward = float(delivered - queue_cost - self.drop_penalty * dropped)
        self.total_dropped += dropped
        self.total_delivered += delivered
        self.step_index += 1

        terminated = bool(
            self.drop_termination_threshold is not None
            and self.total_dropped >= self.drop_termination_threshold
        )
        truncated = bool(not terminated and self.step_index >= self.horizon)
        info = {
            "arrival": arrival,
            "delivered": delivered,
            "dropped": dropped,
            "queue_a": self.queue_a,
            "queue_b": self.queue_b,
            "phase": phase,
            "applied_action": int(action),
            "action_allowed": True,
            "action_mask": self.action_mask().tolist(),
            "total_dropped": self.total_dropped,
            "total_delivered": self.total_delivered,
            "termination_reason": "drop_budget" if terminated else None,
        }
        return self._observation(), reward, terminated, truncated, info


class QNetwork(nn.Module):
    def __init__(
        self, observation_size: int = OBSERVATION_SIZE, action_count: int = 2
    ) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(observation_size, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, action_count),
        )

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.layers(observations)


@dataclass(frozen=True)
class DQNConfig:
    seed: int = 7
    episodes: int = 180
    horizon: int = 48
    gamma: float = 0.96
    learning_rate: float = 1e-3
    replay_capacity: int = 5_000
    warmup_steps: int = 128
    batch_size: int = 64
    target_sync_steps: int = 160
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay_steps: int = 5_000
    drop_termination_threshold: int | None = 20
    drop_penalty: float = 4.0


@dataclass
class TrainingResult:
    model: QNetwork
    episode_returns: list[float]
    losses: list[float]
    steps: int
    final_epsilon: float
    config: DQNConfig

    def metadata(self) -> dict[str, Any]:
        return {
            "config": asdict(self.config),
            "steps": self.steps,
            "final_epsilon": self.final_epsilon,
            "last_20_episode_mean": fmean(self.episode_returns[-20:]),
            "loss_count": len(self.losses),
        }


Transition = tuple[np.ndarray, int, float, np.ndarray, bool]


def epsilon_at(step: int, config: DQNConfig) -> float:
    fraction = min(max(step, 0) / max(config.epsilon_decay_steps, 1), 1.0)
    return config.epsilon_start + fraction * (config.epsilon_end - config.epsilon_start)


def bellman_targets(
    rewards: torch.Tensor,
    next_q: torch.Tensor,
    terminated: torch.Tensor,
    gamma: float,
) -> torch.Tensor:
    """Bootstrap after truncation, but never after a natural termination."""

    return rewards + gamma * (1.0 - terminated) * next_q


def _masked_argmax(q_values: torch.Tensor, observation: np.ndarray) -> int:
    mask = torch.as_tensor(action_mask_from_observation(observation))
    masked = q_values.masked_fill(~mask, -torch.inf)
    return int(masked.argmax().item())


def _optimize(
    *,
    online: QNetwork,
    target: QNetwork,
    optimizer: torch.optim.Optimizer,
    replay: deque[Transition],
    sampler: random.Random,
    config: DQNConfig,
) -> float:
    batch = sampler.sample(list(replay), config.batch_size)
    observations = torch.as_tensor(
        np.stack([item[0] for item in batch]), dtype=torch.float32
    )
    actions = torch.as_tensor([item[1] for item in batch], dtype=torch.int64)
    rewards = torch.as_tensor([item[2] for item in batch], dtype=torch.float32)
    next_observations = torch.as_tensor(
        np.stack([item[3] for item in batch]), dtype=torch.float32
    )
    terminated = torch.as_tensor([item[4] for item in batch], dtype=torch.float32)

    selected_q = online(observations).gather(1, actions[:, None]).squeeze(1)
    with torch.no_grad():
        next_action_masks = next_observations[:, [AVAILABLE_A, AVAILABLE_B]] >= 0.5
        next_q = (
            target(next_observations)
            .masked_fill(~next_action_masks, torch.finfo(torch.float32).min)
            .max(dim=1)
            .values
        )
        targets = bellman_targets(rewards, next_q, terminated, config.gamma)
    loss = nn.functional.smooth_l1_loss(selected_q, targets)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    nn.utils.clip_grad_norm_(online.parameters(), max_norm=5.0)
    optimizer.step()
    return float(loss.detach().item())


def train_dqn(config: DQNConfig = DQNConfig()) -> TrainingResult:
    """Train a small DQN with a safety mask, replay, and a target network."""

    if not 0.0 <= config.gamma <= 1.0:
        raise ValueError("gamma must be between zero and one")
    if config.batch_size > config.replay_capacity:
        raise ValueError("batch_size cannot exceed replay_capacity")
    if not math.isfinite(config.drop_penalty) or config.drop_penalty < 0.0:
        raise ValueError("drop_penalty must be finite and non-negative")
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    sampler = random.Random(config.seed)
    env = RelayQueueEnv(
        horizon=config.horizon,
        drop_termination_threshold=config.drop_termination_threshold,
        drop_penalty=config.drop_penalty,
    )
    online = QNetwork()
    target = QNetwork()
    target.load_state_dict(online.state_dict())
    target.eval()
    optimizer = torch.optim.Adam(online.parameters(), lr=config.learning_rate)
    replay: deque[Transition] = deque(maxlen=config.replay_capacity)
    returns: list[float] = []
    losses: list[float] = []
    global_step = 0

    for episode in range(config.episodes):
        observation, _ = env.reset(seed=config.seed + episode)
        episode_return = 0.0
        while True:
            epsilon = epsilon_at(global_step, config)
            available = np.flatnonzero(action_mask_from_observation(observation))
            if sampler.random() < epsilon:
                action = int(sampler.choice(available.tolist()))
            else:
                with torch.no_grad():
                    tensor = torch.as_tensor(observation, dtype=torch.float32)
                    action = _masked_argmax(online(tensor), observation)

            next_observation, reward, terminated, truncated, _ = env.step(action)
            replay.append(
                (
                    observation.copy(),
                    action,
                    reward,
                    next_observation.copy(),
                    bool(terminated),
                )
            )
            observation = next_observation
            episode_return += reward
            global_step += 1

            if global_step >= config.warmup_steps and len(replay) >= config.batch_size:
                losses.append(
                    _optimize(
                        online=online,
                        target=target,
                        optimizer=optimizer,
                        replay=replay,
                        sampler=sampler,
                        config=config,
                    )
                )
            if global_step % config.target_sync_steps == 0:
                target.load_state_dict(online.state_dict())
            if terminated or truncated:
                break
        returns.append(episode_return)

    env.close()
    return TrainingResult(
        model=online.eval(),
        episode_returns=returns,
        losses=losses,
        steps=global_step,
        final_epsilon=epsilon_at(global_step, config),
        config=config,
    )


Policy = Callable[[np.ndarray, random.Random], int]


def random_policy(observation: np.ndarray, rng: random.Random) -> int:
    actions = np.flatnonzero(action_mask_from_observation(observation)).tolist()
    return int(rng.choice(actions))


def projected_queue_policy(observation: np.ndarray, rng: random.Random) -> int:
    """Observation-only, model-informed reference controller."""

    del rng
    projected = projected_queue_loads(observation)
    mask = action_mask_from_observation(observation)
    candidates = [action for action in (0, 1) if bool(mask[action])]
    return min(candidates, key=lambda action: (float(projected[action]), action))


def always_relay_a_policy(observation: np.ndarray, rng: random.Random) -> int:
    """Deliberately unsafe proposal policy used to prove the filter boundary."""

    del observation, rng
    return 0


def dqn_policy(model: QNetwork) -> Policy:
    def choose(observation: np.ndarray, rng: random.Random) -> int:
        del rng
        with torch.no_grad():
            tensor = torch.as_tensor(observation, dtype=torch.float32)
            return _masked_argmax(model(tensor), observation)

    return choose


def evaluate_policy(
    policy: Policy,
    *,
    seeds: Iterable[int] = range(1_000, 1_040),
    horizon: int = 48,
    queue_capacity: int = 10,
    drop_termination_threshold: int | None = 20,
    drop_penalty: float = 4.0,
    arrival_pattern: Sequence[int] = ARRIVAL_PATTERN,
    service_a_pattern: Sequence[int] = SERVICE_A_PATTERN,
    service_b_pattern: Sequence[int] = SERVICE_B_PATTERN,
    outage_pattern: Sequence[int | None] = DEFAULT_OUTAGE_PATTERN,
) -> dict[str, float]:
    returns: list[float] = []
    dropped: list[float] = []
    delivered: list[float] = []
    blocked: list[float] = []
    applied_constraint_violations = 0
    total_steps = 0
    for seed in seeds:
        env = RelayQueueEnv(
            horizon=horizon,
            queue_capacity=queue_capacity,
            drop_termination_threshold=drop_termination_threshold,
            drop_penalty=drop_penalty,
            arrival_pattern=arrival_pattern,
            service_a_pattern=service_a_pattern,
            service_b_pattern=service_b_pattern,
            outage_pattern=outage_pattern,
        )
        observation, _ = env.reset(seed=int(seed))
        rng = random.Random(int(seed))
        total_return = 0.0
        episode_blocked = 0
        while True:
            proposed_action = int(policy(observation, rng))
            action, was_blocked = filter_action(proposed_action, observation)
            if not bool(action_mask_from_observation(observation)[action]):
                applied_constraint_violations += 1
            episode_blocked += int(was_blocked)
            total_steps += 1
            observation, reward, terminated, truncated, info = env.step(action)
            total_return += reward
            if terminated or truncated:
                returns.append(total_return)
                dropped.append(float(info["total_dropped"]))
                delivered.append(float(info["total_delivered"]))
                blocked.append(float(episode_blocked))
                break
        env.close()
    return {
        "mean_return": fmean(returns),
        "return_std": pstdev(returns),
        "mean_dropped": fmean(dropped),
        "mean_delivered": fmean(delivered),
        "mean_blocked_proposals": fmean(blocked),
        "blocked_proposal_rate": sum(blocked) / total_steps,
        "applied_constraint_violations": float(applied_constraint_violations),
        "episodes": float(len(returns)),
    }


def run_comparison(config: DQNConfig = DQNConfig()) -> dict[str, Any]:
    training = train_dqn(config)
    seeds = range(1_000, 1_040)
    metrics = {
        "random": evaluate_policy(
            random_policy,
            seeds=seeds,
            horizon=config.horizon,
            drop_penalty=config.drop_penalty,
        ),
        "projected_queue": evaluate_policy(
            projected_queue_policy,
            seeds=seeds,
            horizon=config.horizon,
            drop_penalty=config.drop_penalty,
        ),
        "dqn": evaluate_policy(
            dqn_policy(training.model),
            seeds=seeds,
            horizon=config.horizon,
            drop_penalty=config.drop_penalty,
        ),
    }
    return {"training": training, "metrics": metrics}


def smoke_check() -> dict[str, Any]:
    result = run_comparison(DQNConfig(episodes=80, epsilon_decay_steps=2_500))
    for metrics in result["metrics"].values():
        assert np.isfinite(metrics["mean_return"])
        assert metrics["episodes"] == 40.0
        assert metrics["applied_constraint_violations"] == 0.0
    assert result["training"].losses
    return result


if __name__ == "__main__":
    result = run_comparison()
    print(result["training"].metadata())
    print(result["metrics"])
