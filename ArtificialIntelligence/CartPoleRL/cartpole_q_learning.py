"""Train a CartPole-v1 agent with discretized-state Q-learning.

This script keeps the implementation intentionally lightweight so it can run
quickly on modest CPUs while demonstrating a full reinforcement-learning loop.
"""
from __future__ import annotations

import argparse
import dataclasses
import random
from typing import Iterable, Tuple

import numpy as np
try:  # Gymnasium compatibility
    import gymnasium as gym  # type: ignore
except ImportError:
    import gym  # type: ignore


@dataclasses.dataclass
class TrainingConfig:
    """
    Docstring for TrainingConfig.
    """
    episodes: int = 500
    max_steps_per_episode: int = 500
    learning_rate: float = 0.1
    discount_factor: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.995
    bins: Tuple[int, int, int, int] = (6, 12, 6, 12)
    seed: int | None = 123


class StateDiscretizer:
    """Convert continuous CartPole observations into discrete buckets."""

    def __init__(self, bins: Iterable[int]):
        """
        Docstring for __init__.
        """
        self.bins = np.array(list(bins), dtype=np.int32)
        if len(self.bins) != 4:
            raise ValueError("CartPole has exactly four observation dimensions")
        # Reasonable clipping bounds for CartPole (to avoid inf)
        self.low = np.array([-4.8, -5.0, -0.418, -5.0])
        self.high = np.array([4.8, 5.0, 0.418, 5.0])

    def discretize(self, observation: np.ndarray) -> Tuple[int, ...]:
        """
        Docstring for discretize.
        """
        clipped = np.clip(observation, self.low, self.high)
        ratios = (clipped - self.low) / (self.high - self.low)
        buckets = (ratios * self.bins).astype(int)
        buckets = np.clip(buckets, 0, self.bins - 1)
        return tuple(buckets.tolist())


class QLearningAgent:
    """Tabular Q-learning agent with epsilon-greedy exploration."""

    def __init__(self, config: TrainingConfig, discretizer: StateDiscretizer, action_space: gym.Space):
        """
        Docstring for __init__.
        """
        self.cfg = config
        self.discretizer = discretizer
        if not isinstance(action_space.n, (int, np.integer)):
            raise ValueError("CartPole action space must be discrete")
        self.n_actions = int(action_space.n)
        self.q_table = np.zeros((*discretizer.bins, self.n_actions), dtype=np.float32)
        self.epsilon = config.epsilon_start
        if config.seed is not None:
            random.seed(config.seed)
            np.random.seed(config.seed)

    def select_action(self, state: Tuple[int, ...]) -> int:
        """
        Docstring for select_action.
        """
        if random.random() < self.epsilon:
            return random.randrange(self.n_actions)
        return int(np.argmax(self.q_table[state]))

    def update(self, state: Tuple[int, ...], action: int, reward: float, next_state: Tuple[int, ...], done: bool) -> None:
        """
        Docstring for update.
        """
        old_value = self.q_table[state + (action,)]
        next_max = 0.0 if done else float(np.max(self.q_table[next_state]))
        target = reward + self.cfg.discount_factor * next_max
        self.q_table[state + (action,)] = (1 - self.cfg.learning_rate) * old_value + self.cfg.learning_rate * target

    def decay_epsilon(self) -> None:
        """
        Docstring for decay_epsilon.
        """
        self.epsilon = max(self.cfg.epsilon_end, self.epsilon * self.cfg.epsilon_decay)


def run_episode(env: gym.Env, agent: QLearningAgent, cfg: TrainingConfig) -> float:
    """
    Docstring for run_episode.
    """
    obs, _ = env.reset()
    state = agent.discretizer.discretize(np.array(obs, dtype=np.float32))
    total_reward = 0.0

    for _ in range(cfg.max_steps_per_episode):
        action = agent.select_action(state)
        step_result = env.step(action)
        # Gym v0.26 returns (obs, reward, terminated, truncated, info)
        if len(step_result) == 5:
            next_obs, reward, terminated, truncated, _ = step_result
            done = terminated or truncated
        else:  # Fallback for older gym versions
            next_obs, reward, done, _ = step_result
        next_state = agent.discretizer.discretize(np.array(next_obs, dtype=np.float32))
        agent.update(state, action, float(reward), next_state, done)
        total_reward += float(reward)
        state = next_state
        if done:
            break

    agent.decay_epsilon()
    return total_reward


def train(config: TrainingConfig) -> None:
    """
    Docstring for train.
    """
    env = gym.make("CartPole-v1")
    env.reset(seed=config.seed)
    discretizer = StateDiscretizer(config.bins)
    agent = QLearningAgent(config, discretizer, env.action_space)

    rewards = []
    for episode in range(1, config.episodes + 1):
        episode_reward = run_episode(env, agent, config)
        rewards.append(episode_reward)
        print(f"Episode {episode:4d} | Reward: {episode_reward:6.1f} | Epsilon: {agent.epsilon: .3f}")
        if episode % 50 == 0:
            avg_last_50 = sum(rewards[-50:]) / 50.0
            print(f"  Average reward over last 50 episodes: {avg_last_50:.2f}")

    env.close()


def parse_args() -> TrainingConfig:
    """
    Docstring for parse_args.
    """
    parser = argparse.ArgumentParser(description="Train a CartPole-v1 agent with Q-learning")
    parser.add_argument("--episodes", type=int, default=TrainingConfig.episodes, help="Number of training episodes")
    parser.add_argument("--max-steps", type=int, default=TrainingConfig.max_steps_per_episode, help="Max steps per episode")
    parser.add_argument("--lr", type=float, default=TrainingConfig.learning_rate, help="Learning rate for Q-updates")
    parser.add_argument("--gamma", type=float, default=TrainingConfig.discount_factor, help="Discount factor")
    parser.add_argument("--epsilon-start", type=float, default=TrainingConfig.epsilon_start, help="Initial epsilon for exploration")
    parser.add_argument("--epsilon-end", type=float, default=TrainingConfig.epsilon_end, help="Minimum epsilon")
    parser.add_argument("--epsilon-decay", type=float, default=TrainingConfig.epsilon_decay, help="Multiplicative epsilon decay per episode")
    parser.add_argument("--seed", type=int, default=TrainingConfig.seed, help="Random seed (set -1 to disable)")
    args = parser.parse_args()

    seed = None if args.seed < 0 else args.seed
    return TrainingConfig(
        episodes=args.episodes,
        max_steps_per_episode=args.max_steps,
        learning_rate=args.lr,
        discount_factor=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay,
        seed=seed,
    )


if __name__ == "__main__":
    train(parse_args())
