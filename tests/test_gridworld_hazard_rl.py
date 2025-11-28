from __future__ import annotations

import numpy as np

from ArtificialIntelligence.gridworld_hazard_rl import (
    Gridworld,
    TrainingConfig,
    initialize_q_table,
    train_agent,
    update_q_value,
)


def test_q_update_matches_expected_formula() -> None:
    env = Gridworld(width=3, height=3, start=(0, 0), goal=(2, 2), hazards=[], step_penalty=0.0)
    q_table = initialize_q_table(env)
    config = TrainingConfig(
        episodes=1,
        max_steps=1,
        learning_rate=0.5,
        discount_factor=0.9,
        epsilon_start=0.0,
        epsilon_end=0.0,
        epsilon_decay=1.0,
        seed=123,
    )

    state = (0, 0)
    action = 3  # Move right
    next_state = (1, 0)
    reward = 1.0
    q_table[0, 1, :] = [0.8, 0.4, -0.2, 0.1]

    update_q_value(q_table, state, action, reward, next_state, False, config)

    expected = 0.0 + config.learning_rate * (reward + config.discount_factor * 0.8 - 0.0)
    assert np.isclose(q_table[0, 0, action], expected)


def test_agent_learns_to_avoid_hazardous_cell() -> None:
    env = Gridworld(
        width=3,
        height=3,
        start=(0, 1),
        goal=(2, 1),
        hazards=[(1, 1)],
        hazard_penalty=-5.0,
        step_penalty=-0.1,
        goal_reward=5.0,
    )
    config = TrainingConfig(
        episodes=400,
        max_steps=8,
        learning_rate=0.2,
        discount_factor=0.9,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=0.98,
        seed=7,
    )

    q_table = train_agent(env, config)
    start_row, start_col = 1, 0
    right_value = q_table[start_row, start_col, 3]  # Hazard is directly to the right
    safest_value = np.max(np.delete(q_table[start_row, start_col], 3))

    assert safest_value > right_value, "Agent should prefer routes that avoid the hazard"
