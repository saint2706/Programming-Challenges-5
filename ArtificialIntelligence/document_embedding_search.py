"""
Artificial Intelligence project implementation.
"""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


Embedder = Callable[[Sequence[str]], np.ndarray]


@dataclass
class SearchResult:
    """Represents a single search hit."""

    document_id: str
    text: str
    score: float


class DocumentEmbeddingSearch:
    """Embed documents and perform similarity search.

    The class supports a simple in-memory backend along with optional FAISS and
    Annoy indexes for approximate nearest neighbor search.

    Args:
        model_name: Name of the sentence-transformer model to load when an
            embedder is not provided.
        backend: One of ``"naive"``, ``"faiss"``, or ``"annoy"``.
        embedder: Optional callable that returns an ``(n, d)`` numpy array for a
            sequence of texts. If omitted, a sentence-transformer model is
            loaded.
        annoy_trees: Number of trees to build when using Annoy.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        backend: str = "naive",
        embedder: Embedder | None = None,
        annoy_trees: int = 10,
    ) -> None:
        """
        Docstring for __init__.
        """
        self.backend = backend
        self.annoy_trees = annoy_trees
        self.documents: list[str] = []
        self.document_ids: list[str] = []
        self._dimension: int | None = None
        self._embeddings: list[np.ndarray] = []
        self._faiss_index = None
        self._annoy_index = None
        self._embedder = embedder or self._build_sentence_transformer_embedder(
            model_name
        )

    def _build_sentence_transformer_embedder(self, model_name: str) -> Embedder:
        """Create an embedder using a sentence-transformer model."""

        if importlib.util.find_spec("sentence_transformers") is None:
            raise ImportError(
                "sentence-transformers is required when no custom embedder is provided. "
                "Install with `pip install sentence-transformers`."
            )

        sentence_transformers = importlib.import_module("sentence_transformers")
        model = sentence_transformers.SentenceTransformer(model_name)

        def embed(texts: Sequence[str]) -> np.ndarray:
            """
            Docstring for embed.
            """
            return model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)

        return embed

    @staticmethod
    def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """
        Docstring for _normalize_embeddings.
        """
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return embeddings / norms

    def add_documents(self, documents: Sequence[str], ids: Sequence[str] | None = None) -> None:
        """Add new documents to the index."""

        document_ids = [str(idx) for idx, _ in enumerate(documents, start=len(self.documents))]
        if ids is not None:
            if len(ids) != len(documents):
                raise ValueError("ids and documents must be the same length")
            document_ids = list(ids)

        embeddings = self._embedder(documents)
        if embeddings.ndim != 2:
            raise ValueError("Embedder must return a 2D array")

        if self._dimension is None:
            self._dimension = embeddings.shape[1]
        elif embeddings.shape[1] != self._dimension:
            raise ValueError("All embeddings must have the same dimensionality")

        self.documents.extend(documents)
        self.document_ids.extend(document_ids)

        if self.backend == "naive":
            self._embeddings.append(embeddings.astype(np.float32))
        elif self.backend == "faiss":
            self._add_to_faiss_index(embeddings.astype(np.float32))
        elif self.backend == "annoy":
            self._add_to_annoy_index(embeddings.astype(np.float32))
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def query(self, query_text: str, top_k: int = 3) -> list[SearchResult]:
        """Return the top-K most similar documents for a query."""

        if not self.documents:
            return []

        query_vector = self._embedder([query_text]).astype(np.float32)
        query_vector = self._normalize_embeddings(query_vector)

        if self.backend == "naive":
            return self._query_naive(query_vector, top_k)
        if self.backend == "faiss":
            return self._query_faiss(query_vector, top_k)
        return self._query_annoy(query_vector, top_k)

    def _query_naive(self, query_vector: np.ndarray, top_k: int) -> list[SearchResult]:
        """
        Docstring for _query_naive.
        """
        all_embeddings = np.vstack(self._embeddings)
        all_embeddings = self._normalize_embeddings(all_embeddings)
        scores = all_embeddings @ query_vector.T
        scores = scores.reshape(-1)
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            SearchResult(
                document_id=self.document_ids[idx],
                text=self.documents[idx],
                score=float(scores[idx]),
            )
            for idx in top_indices
        ]

    def _add_to_faiss_index(self, embeddings: np.ndarray) -> None:
        """
        Docstring for _add_to_faiss_index.
        """
        if importlib.util.find_spec("faiss") is None:
            raise ImportError("Install faiss-cpu to use the FAISS backend.")

        faiss = importlib.import_module("faiss")
        normalized = self._normalize_embeddings(embeddings)
        if self._faiss_index is None:
            self._faiss_index = faiss.IndexFlatIP(normalized.shape[1])
        self._faiss_index.add(normalized)

    def _query_faiss(self, query_vector: np.ndarray, top_k: int) -> list[SearchResult]:
        """
        Docstring for _query_faiss.
        """
        if self._faiss_index is None:
            return []
        scores, indices = self._faiss_index.search(query_vector, top_k)
        return [
            SearchResult(
                document_id=self.document_ids[idx],
                text=self.documents[idx],
                score=float(scores[0, pos]),
            )
            for pos, idx in enumerate(indices[0])
        ]

    def _add_to_annoy_index(self, embeddings: np.ndarray) -> None:
        """
        Docstring for _add_to_annoy_index.
        """
        if importlib.util.find_spec("annoy") is None:
            raise ImportError("Install annoy to use the Annoy backend.")

        annoy = importlib.import_module("annoy")
        start_index = len(self.documents) - len(embeddings)
        if self._annoy_index is None:
            self._annoy_index = annoy.AnnoyIndex(self._dimension, "angular")
        for offset, vector in enumerate(embeddings):
            self._annoy_index.add_item(start_index + offset, vector.tolist())
        self._annoy_index.build(self.annoy_trees)

    def _query_annoy(self, query_vector: np.ndarray, top_k: int) -> list[SearchResult]:
        """
        Docstring for _query_annoy.
        """
        if self._annoy_index is None:
            return []

        distance_indices, distances = self._annoy_index.get_nns_by_vector(
            query_vector[0].tolist(), top_k, include_distances=True
        )
        return [
            SearchResult(
                document_id=self.document_ids[idx],
                text=self.documents[idx],
                score=1.0 - (distance ** 2) / 2,
            )
            for idx, distance in zip(distance_indices, distances)
        ]


SAMPLE_CORPUS: list[str] = [
    "Sentence embeddings allow semantic search across knowledge bases.",
    "Neural networks learn layered representations of data.",
    "Vector databases make similarity queries fast and scalable.",
    "Reinforcement learning agents optimize behavior through rewards.",
    "Probabilistic models reason about uncertainty in observations.",
]


def demo_query() -> None:
    """Run a small similarity search demo using the sample corpus."""

    search_engine = DocumentEmbeddingSearch()
    search_engine.add_documents(SAMPLE_CORPUS)

    query_text = "How can I search documents using vector embeddings?"
    results = search_engine.query(query_text, top_k=3)
    print(f"Query: {query_text}\n")
    for rank, result in enumerate(results, start=1):
        print(f"{rank}. ({result.score:.3f}) {result.text}")


if __name__ == "__main__":
    demo_query()
