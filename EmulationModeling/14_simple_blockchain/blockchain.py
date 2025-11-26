"""Minimal blockchain implementation with proof-of-work mining."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List


@dataclass
class Block:
    """Represents a single block on the chain."""

    index: int
    timestamp: datetime
    data: Any
    previous_hash: str
    nonce: int = 0
    hash: str = field(init=False, default="")

    def compute_hash(self) -> str:
        """Return the SHA-256 hash of the block's contents."""
        block_dict = {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_dict, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the block for display or storage."""
        return {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }


class Blockchain:
    """Simplified blockchain with proof-of-work mining."""

    def __init__(self, difficulty: int = 4) -> None:
        if difficulty < 1:
            raise ValueError("Difficulty must be a positive integer")
        self.difficulty = difficulty
        self.chain: List[Block] = [self._create_genesis_block()]

    def _create_genesis_block(self) -> Block:
        genesis = Block(
            index=0,
            timestamp=datetime.now(timezone.utc),
            data="Genesis Block",
            previous_hash="0",
        )
        return self._proof_of_work(genesis)

    def _proof_of_work(self, block: Block) -> Block:
        """Iterate the nonce until the block hash meets the difficulty target."""
        prefix = "0" * self.difficulty
        while True:
            block.hash = block.compute_hash()
            if block.hash.startswith(prefix):
                return block
            block.nonce += 1

    def add_block(self, data: Any) -> Block:
        """Create, mine, and append a new block to the chain."""
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now(timezone.utc),
            data=data,
            previous_hash=self.chain[-1].hash,
        )
        mined_block = self._proof_of_work(new_block)
        self.chain.append(mined_block)
        return mined_block

    def is_chain_valid(self) -> bool:
        """Return True if the chain is internally consistent."""
        prefix = "0" * self.difficulty
        for idx, block in enumerate(self.chain):
            recomputed_hash = block.compute_hash()
            if block.hash != recomputed_hash or not block.hash.startswith(prefix):
                return False
            if idx == 0:
                if block.previous_hash != "0":
                    return False
            else:
                if block.previous_hash != self.chain[idx - 1].hash:
                    return False
        return True

    def __repr__(self) -> str:  # pragma: no cover - cosmetic helper
        return f"Blockchain<length={len(self.chain)}, difficulty={self.difficulty}>"
