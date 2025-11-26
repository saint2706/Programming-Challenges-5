import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "EmulationModeling" / "14_simple_blockchain"
sys.path.append(str(MODULE_PATH))

from blockchain import Blockchain  # noqa: E402


def test_chain_stays_valid_when_mined_blocks_added():
    blockchain = Blockchain(difficulty=2)
    blockchain.add_block({"sender": "alice", "receiver": "bob", "amount": 5})
    blockchain.add_block({"sender": "carol", "receiver": "dave", "amount": 7})

    assert len(blockchain.chain) == 3
    assert blockchain.is_chain_valid()


def test_chain_detects_tampering():
    blockchain = Blockchain(difficulty=2)
    blockchain.add_block({"data": "legitimate"})
    blockchain.chain[1].data = "tampered"

    assert not blockchain.is_chain_valid()


def test_invalid_difficulty_raises_value_error():
    with pytest.raises(ValueError):
        Blockchain(difficulty=0)
