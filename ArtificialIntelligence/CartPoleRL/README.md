# CartPole Q-learning Agent

This directory contains a minimal Python implementation of a Q-learning agent that solves OpenAI Gym's `CartPole-v1` task using a discretized observation space.

## Features
- Compatible with both `gym` and `gymnasium` APIs for `CartPole-v1`.
- Discretizes the four-dimensional observation into configurable buckets and stores action values in a tabular Q-table.
- Epsilon-greedy exploration with exponential decay and periodic reward summaries.
- Simple command-line configuration for training duration and learning hyperparameters.

## Dependencies
- Python 3.9+
- `numpy`
- `gym` **or** `gymnasium` (the script tries to import `gymnasium` first and falls back to `gym`)

Example installation with `pip`:

```bash
pip install numpy gym==0.26.2
```

## Usage
Run the training script from this directory (or provide the path):

```bash
python cartpole_q_learning.py --episodes 300 --max-steps 500 --lr 0.1 --gamma 0.99
```

During training, each episode prints its reward and current epsilon value. Every 50 episodes, the script also reports the average reward across the most recent 50 episodes.
