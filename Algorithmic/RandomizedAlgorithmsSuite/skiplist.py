from __future__ import annotations

import random
from typing import Any, Iterable, List, Optional


class SkipListNode:
    def __init__(self, key: Any, value: Any, level: int):
        self.key = key
        self.value = value
        self.forward: List[Optional[SkipListNode]] = [None] * (level + 1)


class SkipList:
    """Probabilistic skip list supporting search, insert, and delete."""

    def __init__(self, p: float = 0.5, max_level: int = 32, rng: Optional[random.Random] = None):
        self.p = p
        self.max_level = max_level
        self.level = 0
        self.header = SkipListNode(None, None, self.max_level)
        self._rng = rng or random.Random()

    def _random_level(self) -> int:
        lvl = 0
        while self._rng.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl

    def search(self, key: Any) -> Optional[Any]:
        current = self.header
        for i in reversed(range(self.level + 1)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        current = current.forward[0]
        if current and current.key == key:
            return current.value
        return None

    def insert(self, key: Any, value: Any) -> None:
        update: List[SkipListNode] = [self.header] * (self.max_level + 1)
        current = self.header
        for i in reversed(range(self.level + 1)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current

        current = current.forward[0]
        if current and current.key == key:
            current.value = value
            return

        lvl = self._random_level()
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.header
            self.level = lvl

        new_node = SkipListNode(key, value, lvl)
        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node

    def delete(self, key: Any) -> bool:
        update: List[SkipListNode] = [self.header] * (self.max_level + 1)
        current = self.header
        for i in reversed(range(self.level + 1)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current

        current = current.forward[0]
        if current and current.key == key:
            for i in range(self.level + 1):
                if update[i].forward[i] != current:
                    continue
                update[i].forward[i] = current.forward[i]
            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1
            return True
        return False

    def __iter__(self):
        node = self.header.forward[0]
        while node:
            yield node.key, node.value
            node = node.forward[0]

    def keys(self) -> Iterable[Any]:
        for key, _ in self:
            yield key

    def values(self) -> Iterable[Any]:
        for _, value in self:
            yield value
