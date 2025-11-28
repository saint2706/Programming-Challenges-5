"""Personalized study planner using a tiny regression model.

This module simulates flashcard review histories, builds feature matrices, and
trains a lightweight regression model to estimate the next review interval.
It is intentionally dependency-light so it can run in constrained environments
without pulling in scikit-learn.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass
class ReviewRecord:
    """Container for a single flashcard review event."""

    card_id: int
    review_index: int
    difficulty: float
    last_interval: float
    correct_streak: int
    incorrect_streak: int
    is_correct: bool
    next_interval: float
    recall_probability: float


def simulate_flashcard_history(
    num_cards: int = 120,
    reviews_per_card: int = 6,
    seed: int | None = 42,
) -> List[ReviewRecord]:
    """Simulate historical flashcard reviews.

    The simulation produces review records with spaced-repetition-like dynamics.

    Args:
        num_cards: How many distinct flashcards to simulate.
        reviews_per_card: How many reviews each card should have.
        seed: Optional seed for reproducibility.

    Returns:
        A list of :class:`ReviewRecord` instances describing each review.
    """

    rng = np.random.default_rng(seed)
    history: List[ReviewRecord] = []

    for card_id in range(num_cards):
        difficulty = float(rng.uniform(0.25, 0.85))
        last_interval = float(rng.uniform(0.8, 2.2))
        correct_streak = 0
        incorrect_streak = 0

        for review_index in range(reviews_per_card):
            recall_probability = float(np.exp(-difficulty * last_interval / 5))
            is_correct = bool(rng.random() < recall_probability)

            if is_correct:
                correct_streak += 1
                incorrect_streak = 0
                growth = 1.6 + 0.15 * rng.random() + 0.05 * correct_streak
                next_interval = last_interval * growth
            else:
                incorrect_streak += 1
                correct_streak = 0
                shrink = 0.6 - 0.08 * rng.random()
                next_interval = max(1.0, last_interval * shrink)

            history.append(
                ReviewRecord(
                    card_id=card_id,
                    review_index=review_index,
                    difficulty=difficulty,
                    last_interval=last_interval,
                    correct_streak=correct_streak,
                    incorrect_streak=incorrect_streak,
                    is_correct=is_correct,
                    next_interval=next_interval,
                    recall_probability=recall_probability,
                )
            )

            last_interval = next_interval

    return history


def build_feature_matrix(
    history: Iterable[ReviewRecord],
) -> Tuple[np.ndarray, np.ndarray]:
    """Convert review history to features and targets.

    Features capture the state before scheduling the next review. The target is
    the simulated next interval.

    Args:
        history: Iterable of :class:`ReviewRecord` instances.

    Returns:
        A tuple ``(X, y)`` where ``X`` is a 2D feature matrix and ``y`` is a 1D
        vector of next-interval targets.
    """

    feature_rows: List[List[float]] = []
    targets: List[float] = []

    for record in history:
        feature_rows.append(
            [
                record.last_interval,
                record.difficulty,
                record.correct_streak,
                record.incorrect_streak,
                record.recall_probability,
            ]
        )
        targets.append(record.next_interval)

    X = np.asarray(feature_rows, dtype=float)
    y = np.asarray(targets, dtype=float)
    return X, y


@dataclass
class LinearIntervalRegressor:
    """A minimal linear regressor with bias handling."""

    weights: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Estimate weights using a least-squares solution."""

        X_bias = np.column_stack([np.ones(len(X)), X])
        self.weights = np.linalg.lstsq(X_bias, y, rcond=None)[0]

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict next intervals given feature matrix ``X``."""

        if self.weights is None:
            raise ValueError("Model is not fitted yet.")

        X_bias = np.column_stack([np.ones(len(X)), X])
        predictions = X_bias @ self.weights
        return np.clip(predictions, 1.0, None)


def train_interval_model(
    history: Iterable[ReviewRecord],
    model: LinearIntervalRegressor | None = None,
) -> LinearIntervalRegressor:
    """Train a linear regressor on the provided history."""

    X, y = build_feature_matrix(history)
    regressor = model or LinearIntervalRegressor()
    regressor.fit(X, y)
    return regressor


def schedule_next_reviews(
    model: LinearIntervalRegressor, samples: Sequence[ReviewRecord]
) -> pd.DataFrame:
    """Generate a schedule for the provided sample cards."""

    X, _ = build_feature_matrix(samples)
    predictions = model.predict(X)
    today = datetime.utcnow()

    rows = []
    for record, predicted_interval in zip(samples, predictions):
        rows.append(
            {
                "card_id": record.card_id,
                "last_interval_days": round(record.last_interval, 2),
                "predicted_interval_days": round(float(predicted_interval), 2),
                "next_review_date": today + timedelta(days=float(predicted_interval)),
            }
        )

    return pd.DataFrame(rows)


def _demo() -> None:
    """Train the model and print an example schedule."""

    history = simulate_flashcard_history()
    model = train_interval_model(history)

    last_reviews = {}
    for record in history:
        last_reviews[record.card_id] = record

    sample_cards = list(last_reviews.values())[:5]
    schedule = schedule_next_reviews(model, sample_cards)
    print("Example schedule for the first five cards:\n")
    print(schedule.to_string(index=False))


if __name__ == "__main__":
    _demo()
