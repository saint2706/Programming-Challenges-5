from __future__ import annotations

"""Tabular Q-learning in a gridworld with hazardous cells.

The environment is a simple 2D grid with a single start, goal, and one or
more hazardous cells that deliver a strong negative reward and end the
episode. The script exposes a CLI for running training and printing the
resulting greedy policy.
"""

import argparse
import dataclasses
import random
from typing import Iterable, List, Sequence, Tuple

import numpy as np

# (dy, dx) order for matrix-friendly indexing (row, column)
ACTIONS: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]
ACTION_SYMBOLS = {0: "^", 1: "v", 2: "<", 3: ">"}


@dataclasses.dataclass
class Gridworld:
    """Simple gridworld with start, goal, and hazardous cells."""

    width: int
    height: int
    start: Tuple[int, int]
    goal: Tuple[int, int]
    hazards: Iterable[Tuple[int, int]]
    step_penalty: float = -0.1
    hazard_penalty: float = -5.0
    goal_reward: float = 10.0

    def __post_init__(self) -> None:
        self.hazards = set(self.hazards)
        for point in (self.start, self.goal, *self.hazards):
            self._ensure_in_bounds(point)
        if self.start in self.hazards:
            raise ValueError("Start cell cannot be hazardous")
        if self.goal in self.hazards:
            raise ValueError("Goal cell cannot be hazardous")

    def _ensure_in_bounds(self, point: Tuple[int, int]) -> None:
        x, y = point
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Point {point} is outside the grid")

    def reset(self) -> Tuple[int, int]:
        """Return the initial state."""

        return self.start

    def step(self, state: Tuple[int, int], action: int) -> Tuple[Tuple[int, int], float, bool]:
        """Apply an action and return the transition.

        Args:
            state: Current ``(x, y)`` location.
            action: Index into :data:`ACTIONS`.

        Returns:
            A tuple ``(next_state, reward, done)``.
        """

        if action not in range(len(ACTIONS)):
            raise ValueError(f"Invalid action index {action}")

        dx, dy = ACTIONS[action][1], ACTIONS[action][0]
        x, y = state
        x, y = x + dx, y + dy
        x = min(max(x, 0), self.width - 1)
        y = min(max(y, 0), self.height - 1)
        next_state = (x, y)

        if next_state in self.hazards:
            return next_state, self.hazard_penalty, True
        if next_state == self.goal:
            return next_state, self.goal_reward, True
        return next_state, self.step_penalty, False


def state_to_indices(state: Tuple[int, int]) -> Tuple[int, int]:
    """Convert ``(x, y)`` coordinates to matrix indices ``(row, col)``."""

    x, y = state
    return y, x


@dataclasses.dataclass
class TrainingConfig:
    """Hyperparameters for Q-learning."""

    episodes: int = 500
    max_steps: int = 200
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.99
    seed: int | None = 0


def initialize_q_table(env: Gridworld) -> np.ndarray:
    """Create an all-zero Q-table shaped ``(height, width, actions)``."""

    return np.zeros((env.height, env.width, len(ACTIONS)), dtype=np.float32)


def epsilon_greedy(q_table: np.ndarray, state: Tuple[int, int], epsilon: float) -> int:
    """Choose an action using epsilon-greedy exploration."""

    if random.random() < epsilon:
        return random.randrange(len(ACTIONS))
    row, col = state_to_indices(state)
    return int(np.argmax(q_table[row, col]))


def update_q_value(
    q_table: np.ndarray,
    state: Tuple[int, int],
    action: int,
    reward: float,
    next_state: Tuple[int, int],
    done: bool,
    config: TrainingConfig,
) -> None:
    """Perform an in-place Q-learning update."""

    row, col = state_to_indices(state)
    next_row, next_col = state_to_indices(next_state)
    current_value = float(q_table[row, col, action])
    next_max = 0.0 if done else float(np.max(q_table[next_row, next_col]))
    target = reward + config.discount_factor * next_max
    q_table[row, col, action] = current_value + config.learning_rate * (target - current_value)


def train_agent(env: Gridworld, config: TrainingConfig) -> np.ndarray:
    """Run tabular Q-learning and return the learned Q-table."""

    if config.seed is not None:
        random.seed(config.seed)
        np.random.seed(config.seed)

    q_table = initialize_q_table(env)
    epsilon = config.epsilon_start

    for _ in range(config.episodes):
        state = env.reset()
        for _ in range(config.max_steps):
            action = epsilon_greedy(q_table, state, epsilon)
            next_state, reward, done = env.step(state, action)
            update_q_value(q_table, state, action, reward, next_state, done, config)
            state = next_state
            if done:
                break
        epsilon = max(config.epsilon_end, epsilon * config.epsilon_decay)

    return q_table


def derive_policy(env: Gridworld, q_table: np.ndarray) -> List[List[str]]:
    """Derive a greedy policy grid from a trained Q-table."""

    policy: List[List[str]] = []
    for y in range(env.height):
        row_symbols: List[str] = []
        for x in range(env.width):
            state = (x, y)
            if state == env.start:
                row_symbols.append("S")
            elif state == env.goal:
                row_symbols.append("G")
            elif state in env.hazards:
                row_symbols.append("X")
            else:
                action = int(np.argmax(q_table[y, x]))
                row_symbols.append(ACTION_SYMBOLS[action])
        policy.append(row_symbols)
    return policy


def policy_to_string(policy: Sequence[Sequence[str]]) -> str:
    """Convert a policy grid into a printable string representation."""

    return "\n".join(" ".join(row) for row in policy)


def parse_hazards(raw: Sequence[str]) -> List[Tuple[int, int]]:
    """Parse hazard coordinates from CLI input."""

    hazards: List[Tuple[int, int]] = []
    for item in raw:
        try:
            x_str, y_str = item.split(",")
            hazards.append((int(x_str), int(y_str)))
        except ValueError as exc:  # pragma: no cover - user input validation
            raise argparse.ArgumentTypeError(
                f"Invalid hazard coordinate '{item}', expected format x,y"
            ) from exc
    return hazards


def run_cli() -> None:
    """Train an agent from command-line arguments and print the policy."""

    parser = argparse.ArgumentParser(description="Train a Q-learning agent in a hazardous gridworld")
    parser.add_argument("--width", type=int, default=5, help="Grid width")
    parser.add_argument("--height", type=int, default=5, help="Grid height")
    parser.add_argument("--start", type=str, default="0,0", help="Start coordinate as x,y")
    parser.add_argument("--goal", type=str, default="4,4", help="Goal coordinate as x,y")
    parser.add_argument(
        "--hazards",
        type=str,
        nargs="*",
        default=["2,2"],
        help="Hazard coordinates as x,y entries",
    )
    parser.add_argument("--episodes", type=int, default=300, help="Training episodes")
    parser.add_argument("--max-steps", type=int, default=200, help="Maximum steps per episode")
    parser.add_argument("--lr", type=float, default=0.1, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor")
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial epsilon")
    parser.add_argument("--epsilon-end", type=float, default=0.05, help="Final epsilon")
    parser.add_argument("--epsilon-decay", type=float, default=0.99, help="Epsilon decay per episode")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (-1 to disable)")
    args = parser.parse_args()

    start = tuple(int(coord) for coord in args.start.split(","))
    goal = tuple(int(coord) for coord in args.goal.split(","))
    hazards = parse_hazards(args.hazards)
    seed = None if args.seed < 0 else args.seed

    env = Gridworld(
        width=args.width,
        height=args.height,
        start=(start[0], start[1]),
        goal=(goal[0], goal[1]),
        hazards=hazards,
    )
    config = TrainingConfig(
        episodes=args.episodes,
        max_steps=args.max_steps,
        learning_rate=args.lr,
        discount_factor=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay,
        seed=seed,
    )

    q_table = train_agent(env, config)
    policy = derive_policy(env, q_table)
    print("Learned greedy policy (S=start, G=goal, X=hazard):")
    print(policy_to_string(policy))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    run_cli()
