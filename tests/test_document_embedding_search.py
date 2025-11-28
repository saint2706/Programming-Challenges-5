from __future__ import annotations

import numpy as np

from ArtificialIntelligence.document_embedding_search import DocumentEmbeddingSearch


def test_results_are_ordered_by_cosine_similarity() -> None:
    embeddings = {
        "ai overview": np.array([1.0, 0.0], dtype=np.float32),
        "vector search basics": np.array([0.8, 0.2], dtype=np.float32),
        "gardening tips": np.array([0.0, 1.0], dtype=np.float32),
        "semantic query": np.array([1.0, 0.1], dtype=np.float32),
    }

    def embed(texts: list[str]) -> np.ndarray:
        return np.vstack([embeddings[text] for text in texts])

    search = DocumentEmbeddingSearch(embedder=embed)
    corpus = ["ai overview", "vector search basics", "gardening tips"]
    search.add_documents(corpus, ids=["d1", "d2", "d3"])

    results = search.query("semantic query", top_k=3)

    assert [result.document_id for result in results] == ["d1", "d2", "d3"]
    assert results[0].score > results[1].score > results[2].score


def test_top_k_is_capped_by_corpus_size() -> None:
    embeddings = {
        "doc alpha": np.array([0.6, 0.8], dtype=np.float32),
        "doc beta": np.array([0.4, 0.9], dtype=np.float32),
        "broad query": np.array([0.5, 0.5], dtype=np.float32),
    }

    def embed(texts: list[str]) -> np.ndarray:
        return np.vstack([embeddings[text] for text in texts])

    search = DocumentEmbeddingSearch(embedder=embed)
    search.add_documents(["doc alpha", "doc beta"], ids=["alpha", "beta"])

    results = search.query("broad query", top_k=10)

    assert len(results) == 2
    assert {result.document_id for result in results} == {"alpha", "beta"}
