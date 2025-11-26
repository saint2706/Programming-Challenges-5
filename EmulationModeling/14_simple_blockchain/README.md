# Simple Blockchain (Emulation/Modeling Challenge 14)

This challenge implements a minimal blockchain in Python with a proof-of-work consensus simulation. Each `Block` records its index, timestamp, arbitrary data payload, previous block hash, nonce, and resulting hash. Blocks are mined by iterating the nonce until the hash meets the configured difficulty (leading zeros).

## Features
- Genesis block creation with a fixed previous hash of `"0"`.
- Proof-of-work mining that enforces a configurable difficulty.
- Methods to append new blocks after mining and to validate the entire chain's integrity.
- Demonstration script that mines a few sample blocks and prints the resulting chain.

## Usage
```bash
cd EmulationModeling/14_simple_blockchain
python main.py
```

You should see each mined block, a validation check, and the full chain printed as dictionaries.
