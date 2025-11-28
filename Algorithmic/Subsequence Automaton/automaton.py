"""
Implementation of the algorithm.
"""

from typing import Dict, List, Optional

class SubsequenceAutomaton:
    """
    An automaton that allows checking if a string S is a subsequence of T
    in O(|S|) time, after O(|T| * |Sigma|) preprocessing.
    """

    def __init__(self, text: str):
        """
        Docstring for __init__.
        """
        self.text = text
        self.alphabet = sorted(list(set(text)))
        self.next_occurrence: List[Dict[str, int]] = []

        self._build()

    def _build(self):
        """
        Builds the transition table.
        next_occurrence[i][char] stores the index of the first occurrence
        of 'char' in text[i+1:]. If not found, it's not in the dict.
        """
        n = len(self.text)

        # Initialize list of dicts.
        # Size n+1 because state i corresponds to "just matched character at index i-1"
        # State 0 is "start", State 1 is "matched index 0", ..., State n is "matched index n-1"

        # Actually, let's define next_occurrence[i][c] as the index of the first 'c' at or after index i.
        # This makes queries easier.
        # Let's say we are at index `current_index` in T (meaning we have used up to `current_index-1`).
        # We want to find the first 'c' at or after `current_index`.

        # Let's resize to n + 1 for convenience, where index n means "end of string".
        self.next_occurrence = [{} for _ in range(n + 1)]

        # We iterate backwards from the end of the text
        # current_next stores the index of the next seen character
        current_next: Dict[str, int] = {}

        for i in range(n - 1, -1, -1):
            char = self.text[i]

            # For the current position i, the next occurrence of 'char' is i itself.
            # But we also inherit known occurrences from i+1.

            # Copy knowledge from the next state (i+1)
            # This is O(Sigma) copy.
            for c, idx in current_next.items():
                self.next_occurrence[i][c] = idx

            # Update the occurrence for the current character to be i
            self.next_occurrence[i][char] = i
            current_next[char] = i

        # next_occurrence[n] remains empty (no characters after end)

    def is_subsequence(self, query: str) -> bool:
        """
        Checks if 'query' is a subsequence of the original text.
        Time Complexity: O(len(query))
        """
        current_index = 0

        for char in query:
            if current_index >= len(self.text):
                return False

            # Check if there is an occurrence of 'char' at or after current_index
            if char in self.next_occurrence[current_index]:
                # Jump to that index
                found_index = self.next_occurrence[current_index][char]
                # Prepare for next character: must be AFTER found_index
                current_index = found_index + 1
            else:
                return False

        return True

    def find_first_subsequence_indices(self, query: str) -> Optional[List[int]]:
        """
        Returns the indices in T corresponding to the *first* valid embedding of S.
        """
        current_index = 0
        indices = []

        for char in query:
            if current_index >= len(self.text):
                return None

            if char in self.next_occurrence[current_index]:
                found_index = self.next_occurrence[current_index][char]
                indices.append(found_index)
                current_index = found_index + 1
            else:
                return None
        return indices
