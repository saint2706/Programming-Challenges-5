from __future__ import annotations

import hashlib
from bisect import bisect_right
from dataclasses import dataclass
from typing import List, Protocol, Sequence


class HashFunction(Protocol):
    """Protocol for hash functions used by :class:`HashRing`."""

    def __call__(self, value: str) -> int:
        ...


class Sha256Hash:
    """Default hash function using SHA-256."""

    def __call__(self, value: str) -> int:  # pragma: no cover - trivial
        digest = hashlib.sha256(value.encode("utf-8")).digest()
        return int.from_bytes(digest, "big", signed=False)


@dataclass(order=True)
class Bucket:
    hash: int
    node: str
    vnode: int


class HashRing:
    """Consistent hash ring modeled as sorted buckets.

    Each bucket stores ``(hash, node, vnode)`` where ``vnode`` is the
    virtual-node index for the physical node. The ring is kept sorted by hash
    to support efficient lookups with ``bisect``.
    """

    def __init__(self, hash_function: HashFunction | None = None):
        self.hash_function = hash_function or Sha256Hash()
        self._buckets: List[Bucket] = []
        self._hashes: List[int] = []

    @property
    def buckets(self) -> Sequence[Bucket]:
        return tuple(self._buckets)

    def _rebuild_index(self) -> None:
        self._buckets.sort(key=lambda bucket: bucket.hash)
        self._hashes = [bucket.hash for bucket in self._buckets]

    def add_node(self, node: str, vnode_count: int = 100) -> None:
        """Add a physical node with ``vnode_count`` virtual nodes."""
        for vnode in range(vnode_count):
            bucket_hash = self.hash_function(f"{node}#{vnode}")
            self._buckets.append(Bucket(bucket_hash, node, vnode))
        self._rebuild_index()

    def remove_node(self, node: str) -> None:
        """Remove a node and all of its virtual nodes from the ring."""
        self._buckets = [bucket for bucket in self._buckets if bucket.node != node]
        self._rebuild_index()

    def lookup(self, key: str, replicas: int = 1) -> List[str]:
        """Return the primary node followed by replica nodes for ``key``.

        Args:
            key: The lookup key.
            replicas: Number of unique nodes to return (including primary).

        Raises:
            ValueError: If the ring is empty or ``replicas`` is less than 1.
        """

        if replicas < 1:
            raise ValueError("replicas must be at least 1")
        if not self._buckets:
            raise ValueError("hash ring is empty")

        key_hash = self.hash_function(key)
        start = bisect_right(self._hashes, key_hash)

        result: List[str] = []
        visited = 0
        total = len(self._buckets)

        while len(result) < replicas and visited < total:
            bucket = self._buckets[(start + visited) % total]
            if bucket.node not in result:
                result.append(bucket.node)
            visited += 1

        return result
