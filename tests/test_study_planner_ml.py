from __future__ import annotations

import numpy as np

from ArtificialIntelligence.study_planner_ml import (
    build_feature_matrix,
    schedule_next_reviews,
    simulate_flashcard_history,
    train_interval_model,
)


def test_feature_matrix_shapes() -> None:
    history = simulate_flashcard_history(num_cards=5, reviews_per_card=3, seed=7)
    X, y = build_feature_matrix(history)

    assert X.shape == (len(history), 5)
    assert y.shape == (len(history),)
    assert np.all(X[:, 0] > 0)


def test_prediction_shape_and_clip() -> None:
    history = simulate_flashcard_history(num_cards=8, reviews_per_card=4, seed=11)
    model = train_interval_model(history)
    X, _ = build_feature_matrix(history[:10])

    preds = model.predict(X)

    assert preds.shape == (X.shape[0],)
    assert np.all(preds >= 1.0)


def test_schedule_generation_matches_sample_size() -> None:
    history = simulate_flashcard_history(num_cards=4, reviews_per_card=2, seed=5)
    model = train_interval_model(history)
    sample_cards = history[-3:]

    schedule = schedule_next_reviews(model, sample_cards)

    assert len(schedule) == len(sample_cards)
    assert set(schedule.columns) == {
        "card_id",
        "last_interval_days",
        "predicted_interval_days",
        "next_review_date",
    }
