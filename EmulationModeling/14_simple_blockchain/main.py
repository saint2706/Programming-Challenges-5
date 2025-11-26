"""Run a small demo that builds and validates a simple blockchain."""
from __future__ import annotations

from pprint import pprint

from blockchain import Blockchain


def run_demo() -> None:
    blockchain = Blockchain(difficulty=3)

    demo_data = [
        {"sender": "alice", "receiver": "bob", "amount": 25},
        {"sender": "carol", "receiver": "dave", "amount": 12},
        {"sender": "eve", "receiver": "frank", "amount": 8},
    ]

    for entry in demo_data:
        mined_block = blockchain.add_block(entry)
        print(f"Mined block #{mined_block.index} with hash {mined_block.hash}")

    print("\nBlockchain valid:", blockchain.is_chain_valid())
    print("\nFull chain:")
    for block in blockchain.chain:
        pprint(block.to_dict())


if __name__ == "__main__":
    run_demo()
