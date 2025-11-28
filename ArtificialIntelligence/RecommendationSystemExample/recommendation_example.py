"""
A small, self-contained recommendation demo that combines collaborative filtering and content-based suggestions.
Run directly to see recommendations for a sample user.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def cosine_similarity(matrix: np.ndarray) -> np.ndarray:
    """Compute cosine similarity for rows in a matrix."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    # Avoid division by zero for all-zero rows
    safe_matrix = np.divide(
        matrix, norms, out=np.zeros_like(matrix, dtype=float), where=norms != 0
    )
    return safe_matrix @ safe_matrix.T


def user_based_recommendations(
    ratings: np.ndarray,
    user_index: int,
    movie_titles: List[str],
    top_k_similar: int = 2,
    top_n: int = 3,
) -> List[Tuple[str, float]]:
    """Recommend movies using user-user cosine similarity."""
    similarity = cosine_similarity(ratings)
    # Exclude self similarity
    similarity[user_index, user_index] = 0
    neighbor_indices = np.argsort(similarity[user_index])[::-1][:top_k_similar]
    neighbor_sims = similarity[user_index, neighbor_indices]

    user_ratings = ratings[user_index]
    unrated_indices = np.where(user_ratings == 0)[0]

    scores = []
    for movie_idx in unrated_indices:
        neighbor_ratings = ratings[neighbor_indices, movie_idx]
        if neighbor_ratings.sum() == 0:
            continue
        weighted_sum = np.dot(neighbor_sims, neighbor_ratings)
        normalization = np.sum(np.abs(neighbor_sims)) or 1
        score = weighted_sum / normalization
        scores.append((movie_idx, score))

    ranked = sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
    return [(movie_titles[idx], round(score, 2)) for idx, score in ranked]


def item_based_recommendations(
    ratings: np.ndarray,
    user_index: int,
    movie_titles: List[str],
    top_k_similar: int = 2,
    top_n: int = 3,
) -> List[Tuple[str, float]]:
    """Recommend movies using item-item cosine similarity."""
    similarity = cosine_similarity(ratings.T)

    user_ratings = ratings[user_index]
    unrated_indices = np.where(user_ratings == 0)[0]

    scores = []
    for movie_idx in unrated_indices:
        item_sims = similarity[movie_idx]
        rated_indices = np.where(user_ratings > 0)[0]
        relevant_sims = item_sims[rated_indices]
        relevant_ratings = user_ratings[rated_indices]
        if relevant_ratings.size == 0:
            continue
        weighted_sum = np.dot(relevant_sims, relevant_ratings)
        normalization = np.sum(np.abs(relevant_sims)) or 1
        score = weighted_sum / normalization
        scores.append((movie_idx, score))

    ranked = sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
    return [(movie_titles[idx], round(score, 2)) for idx, score in ranked]


def content_based_recommendations(
    ratings: np.ndarray,
    user_index: int,
    movie_titles: List[str],
    movie_features: np.ndarray,
    feature_labels: List[str],
    top_n: int = 3,
) -> List[Tuple[str, float]]:
    """Recommend movies using a simple weighted user profile of movie features."""
    user_ratings = ratings[user_index]
    # Build user profile by weighting features with ratings
    rated_mask = user_ratings > 0
    if not np.any(rated_mask):
        return []

    weighted_features = movie_features[rated_mask] * user_ratings[rated_mask][:, None]
    user_profile = weighted_features.mean(axis=0)

    # Cosine similarity between user profile and movie features
    profile_norm = np.linalg.norm(user_profile)
    feature_norms = np.linalg.norm(movie_features, axis=1)
    similarities = np.divide(
        movie_features @ user_profile,
        feature_norms * profile_norm,
        out=np.zeros_like(feature_norms),
        where=feature_norms * profile_norm != 0,
    )

    unrated_indices = np.where(user_ratings == 0)[0]
    ranked_indices = sorted(
        unrated_indices, key=lambda idx: similarities[idx], reverse=True
    )[:top_n]
    return [
        (movie_titles[idx], round(float(similarities[idx]), 2))
        for idx in ranked_indices
    ]


def main() -> None:
    users = ["Alice", "Bob", "Charlie", "Diana"]
    movies = [
        "Action Blast",
        "Romantic Escape",
        "Space Odyssey",
        "Comedy Night",
        "Drama Unfolded",
    ]

    # Rows correspond to users, columns to movies
    ratings = np.array(
        [
            [5, 3, 4, 0, 0],  # Alice
            [4, 0, 5, 2, 1],  # Bob
            [0, 4, 0, 5, 4],  # Charlie
            [3, 5, 0, 4, 0],  # Diana
        ],
        dtype=float,
    )

    # Simple movie features: [Action, Romance, Sci-Fi, Comedy]
    movie_features = np.array(
        [
            [1, 0, 0, 0],  # Action Blast
            [0, 1, 0, 0],  # Romantic Escape
            [0, 0, 1, 0],  # Space Odyssey
            [0.2, 0.2, 0, 1],  # Comedy Night
            [0, 0.8, 0.2, 0],  # Drama Unfolded
        ]
    )
    feature_labels = ["Action", "Romance", "Sci-Fi", "Comedy"]

    sample_user = 0  # Alice
    print(f"Recommendations for {users[sample_user]}:\n")

    user_based = user_based_recommendations(ratings, sample_user, movies)
    print("User-based (cosine):")
    for title, score in user_based:
        print(f"  {title} (predicted rating: {score})")

    item_based = item_based_recommendations(ratings, sample_user, movies)
    print("\nItem-based (cosine):")
    for title, score in item_based:
        print(f"  {title} (predicted rating: {score})")

    content_based = content_based_recommendations(
        ratings, sample_user, movies, movie_features, feature_labels
    )
    print("\nContent-based (features):")
    for title, score in content_based:
        print(f"  {title} (similarity: {score})")


if __name__ == "__main__":
    main()
