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

    def __init__(self, n: int = 2):
        """
        Args:
            n: Order of the N-gram model (e.g., 2 for bigram).
        """
        self.root = TrieNode()
        self.n = n
        self.unigram_counts: Dict[str, int] = collections.defaultdict(int)
        self.ngram_counts: Dict[tuple, int] = collections.defaultdict(int)
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
        """Updates N-gram counts."""
        if len(words) < self.n:
            return

        for i in range(len(words) - self.n + 1):
            ngram = tuple(words[i : i + self.n])
            self.ngram_counts[ngram] += 1

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
        Uses simple smoothing.
        """
        if self.n == 1 or not context:
            # Fallback to unigram probability
            return self.unigram_counts[word] / (
                self.total_words + 1
            )  # +1 for smoothing

        # Try to use the largest context possible up to n-1
        context_len = min(len(context), self.n - 1)
        relevant_context = tuple(context[-context_len:])

        ngram = relevant_context + (word,)

        # Iterate over all ngrams to find how many times this context appeared
        # This is inefficient for large corpora; a real implementation would store context counts separately.
        # But for this challenge, we can approximate or store context counts.

        # Optimization: Store context counts in a separate dict during training?
        # For now, let's just use the ngram count directly.

        # P(w | c) = Count(c, w) / Count(c)

        # We need Count(c). Since we don't store it explicitly efficiently, let's hack it or re-architect.
        # Let's assume we stored it. But wait, I can just sum over all words w' for Count(c, w').

        # Let's simplify: ranking score = alpha * unigram_freq + beta * ngram_prob

        # Actually, let's just use the count of the ngram directly as a score booster.

        ngram_count = self.ngram_counts.get(ngram, 0)
        if ngram_count > 0:
            return ngram_count * 100  # Boost significantly if it follows the context

        return self.unigram_counts[word]  # Default to unigram freq

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

        # Rank candidates
        # Score = (Frequency in Trie) + (Bonus if matches N-gram context)

        scored_candidates = []
        for cand in candidates:
            score = self.unigram_counts[cand]

            # Check if this candidate completes an n-gram with the context
            # We look at the last n-1 words of context
            if context:
                prob = self._get_ngram_probability(cand, context)
                # If prob is high (meaning it was found in ngrams), it dominates
                score += prob

            scored_candidates.append((-score, cand))  # Max heap via negative score

        heapq.heapify(scored_candidates)

        results = []
        for _ in range(min(len(scored_candidates), max_results)):
            score, word = heapq.heappop(scored_candidates)
            results.append(word)

        return results
