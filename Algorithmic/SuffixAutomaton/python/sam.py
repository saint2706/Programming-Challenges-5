"""Suffix Automaton Implementation.

Constructs a Suffix Automaton in O(N) time.
"""

from typing import Dict, List


class State:
    __slots__ = ["len", "link", "next"]

    def __init__(self, length: int = 0, link: int = -1):
        self.len = length
        self.link = link
        self.next: Dict[str, int] = {}


class SuffixAutomaton:
    def __init__(self, s: str = ""):
        self.states: List[State] = [State()]  # Initial state 0
        self.last = 0
        for char in s:
            self.extend(char)

    def extend(self, char: str):
        cur = len(self.states)
        self.states.append(State(self.states[self.last].len + 1))
        p = self.last

        while p != -1 and char not in self.states[p].next:
            self.states[p].next[char] = cur
            p = self.states[p].link

        if p == -1:
            self.states[cur].link = 0
        else:
            q = self.states[p].next[char]
            if self.states[p].len + 1 == self.states[q].len:
                self.states[cur].link = q
            else:
                clone = len(self.states)
                clone_state = State(self.states[p].len + 1, self.states[q].link)
                clone_state.next = self.states[q].next.copy()
                self.states.append(clone_state)

                while p != -1 and self.states[p].next.get(char) == q:
                    self.states[p].next[char] = clone
                    p = self.states[p].link

                self.states[q].link = clone
                self.states[cur].link = clone

        self.last = cur

    def check_substring(self, pattern: str) -> bool:
        cur = 0
        for char in pattern:
            if char not in self.states[cur].next:
                return False
            cur = self.states[cur].next[char]
        return True
