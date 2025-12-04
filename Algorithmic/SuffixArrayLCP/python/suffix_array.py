"""Suffix Array and LCP Array Construction.

Uses O(N log^2 N) prefix doubling construction.
"""

from typing import List, Tuple


class SuffixArray:
    def __init__(self, s: str):
        self.s = s
        self.sa = self._construct_sa(s)
        self.lcp = self._construct_lcp(s, self.sa)

    def _construct_sa(self, s: str) -> List[int]:
        s += "$"
        n = len(s)

        # Rank 0: single characters
        rank = [ord(c) for c in s]
        k = 1

        while k < n:
            # Create tuple (rank[i], rank[i+k]) for sorting
            # If i+k >= n, second part is -1
            tuples = []
            for i in range(n):
                first = rank[i]
                second = rank[i + k] if i + k < n else -1
                tuples.append(((first, second), i))

            # Sort by rank pairs
            tuples.sort()

            # Reassign ranks
            new_rank = [0] * n
            sa = [0] * n

            # First element
            sa[0] = tuples[0][1]
            new_rank[tuples[0][1]] = 0

            for i in range(1, n):
                prev_rank_pair = tuples[i - 1][0]
                curr_rank_pair = tuples[i][0]
                idx = tuples[i][1]
                sa[i] = idx

                if curr_rank_pair == prev_rank_pair:
                    new_rank[idx] = new_rank[tuples[i - 1][1]]
                else:
                    new_rank[idx] = new_rank[tuples[i - 1][1]] + 1

            rank = new_rank
            k *= 2

            if rank[sa[n - 1]] == n - 1:  # All ranks unique
                break

        return sa

    def _construct_lcp(self, s: str, sa: List[int]) -> List[int]:
        n = len(sa)  # Includes $
        rank = [0] * n
        for i in range(n):
            rank[sa[i]] = i

        lcp = [0] * n
        k = 0
        # Kasai's algorithm O(N)
        for i in range(len(s)):  # Iterate original string indices
            if i >= len(rank):
                continue

            r = rank[i]
            if r == n - 1:
                k = 0
                continue

            j = sa[r + 1]

            while i + k < len(s) and j + k < len(s) and s[i + k] == s[j + k]:
                k += 1
            lcp[r] = k
            if k > 0:
                k -= 1
        return lcp
