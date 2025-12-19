import collections
import heapq
from typing import Dict, List, Optional


class TrieNode:
    """A node in the Trie."""

    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.frequency: int = 0
        self.word: Optional[str] = (
            None  # Store the full word at the leaf for convenience
        )


class AutocompleteEngine:
    """
    Autocomplete engine combining Trie-based prefix matching with
    N-gram language model probabilities for ranking.
    """

    def __init__(self, n: int = 2, alpha: float = 0.4):
        """
        Args:
            n: Order of the N-gram model (e.g., 2 for bigram).
            alpha: Weight for unigram probability in interpolation (0.0 to 1.0).
                   Score = alpha * P(w) + (1 - alpha) * P(w|c)
        """
        self.root = TrieNode()
        self.n = n
        self.alpha = alpha
        self.unigram_counts: Dict[str, int] = collections.defaultdict(int)
        self.ngram_counts: Dict[tuple, int] = collections.defaultdict(int)
        self.context_counts: Dict[tuple, int] = collections.defaultdict(int)
        self.total_words = 0

    def train(self, corpus: List[str]):
        """
        Trains the engine with a list of sentences/phrases.

        Args:
            corpus: List of strings (sentences).
        """
        for sentence in corpus:
            words = sentence.lower().split()
            self._insert_words(words)
            self._update_ngrams(words)

    def _insert_words(self, words: List[str]):
        """Inserts words into the Trie and updates unigram counts."""
        for word in words:
            self.total_words += 1
            self.unigram_counts[word] += 1

            node = self.root
            for char in word:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_end_of_word = True
            node.frequency = self.unigram_counts[word]
            node.word = word

    def _update_ngrams(self, words: List[str]):
        """Updates N-gram counts and context counts."""
        if len(words) < self.n:
            return

        for i in range(len(words) - self.n + 1):
            ngram = tuple(words[i : i + self.n])
            self.ngram_counts[ngram] += 1
            context = ngram[:-1]
            self.context_counts[context] += 1

    def _get_candidates_from_trie(self, prefix: str) -> List[str]:
        """Returns all words in the Trie starting with prefix."""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        # DFS to find all words
        results = []
        stack = [node]
        while stack:
            curr = stack.pop()
            if curr.is_end_of_word:
                results.append(curr.word)
            for child in curr.children.values():
                stack.append(child)
        return results

    def _get_ngram_probability(self, word: str, context: List[str]) -> float:
        """
        Calculates P(word | context) using the N-gram model.
        """
        if self.n == 1:
            # For unigram model, conditional probability is just P(w)
            return self.unigram_counts[word] / max(self.total_words, 1)

        # Try to use the largest context possible up to n-1
        context_len = min(len(context), self.n - 1)
        relevant_context = tuple(context[-context_len:])

        # P(w | c) = Count(c, w) / Count(c)
        count_context = self.context_counts.get(relevant_context, 0)

        if count_context == 0:
            return 0.0

        ngram = relevant_context + (word,)
        count_ngram = self.ngram_counts.get(ngram, 0)

        return count_ngram / count_context

    def complete(self, text: str, max_results: int = 5) -> List[str]:
        """
        Provides completions for the last word in the text, considering context.

        Args:
            text: Input text (e.g., "hello wo").
            max_results: Max number of completions.

        Returns:
            List of completed words/phrases.
        """
        words = text.lower().split()
        if not words:
            return []

        prefix = words[-1]
        context = words[:-1]

        candidates = self._get_candidates_from_trie(prefix)

        # Rank candidates using interpolation:
        # Score = alpha * P(w) + (1 - alpha) * P(w | c)

        scored_candidates = []
        for cand in candidates:
            # Unigram probability: P(w)
            p_unigram = self.unigram_counts[cand] / max(self.total_words, 1)

            # Conditional probability: P(w | c)
            p_ngram = 0.0
            if context:
                p_ngram = self._get_ngram_probability(cand, context)

            score = (self.alpha * p_unigram) + ((1 - self.alpha) * p_ngram)

            scored_candidates.append((-score, cand))  # Max heap via negative score

        heapq.heapify(scored_candidates)

        results = []
        for _ in range(min(len(scored_candidates), max_results)):
            score, word = heapq.heappop(scored_candidates)
            results.append(word)

        return results
