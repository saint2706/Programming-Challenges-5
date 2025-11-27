# Recommendation System Example

This example demonstrates three simple recommendation strategies on a tiny user–movie ratings matrix:

- **User-based collaborative filtering (cosine similarity)** to find users with similar taste and predict ratings for items the target user has not rated.
- **Item-based collaborative filtering (cosine similarity)** to compare movies and suggest titles close to those the user enjoyed.
- **Content-based filtering** using a handcrafted feature vector (genres/tones) for each movie to match user preferences.

## How it works

1. A small ratings matrix (users × movies) is loaded in-memory; zeros represent unrated items.
2. Cosine similarity is computed either across users (user-user) or across items (item-item).
3. Unrated movies are scored via similarity-weighted averages of neighbor ratings.
4. For the content-based path, a user preference profile is built by weighting movie features with that user's ratings, then computing cosine similarity with every movie.
5. The script prints top recommendations for a sample user (Alice) from all three strategies.

## Running the demo

From the repository root:

```bash
python ArtificialIntelligence/RecommendationSystemExample/recommendation_example.py
```

The output lists recommendations for the sample user using user-based, item-based, and content-based approaches. Adjust the `ratings`, `movie_features`, or `sample_user` variables inside the script to experiment with different scenarios.
