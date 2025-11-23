# Matching Engine (Order Book)

A Go implementation of a limit order book matching engine.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

A **Matching Engine** maintains a book of buy (bid) and sell (ask) orders.
- **Bids** are stored in a Max-Heap (highest price first).
- **Asks** are stored in a Min-Heap (lowest price first).
- **Matching**: When a new order arrives (e.g., Buy), it attempts to match with the best available Ask. If `BidPrice >= AskPrice`, a trade occurs.
- **Price-Time Priority**: If prices match, older orders (FIFO) are executed first.

## 💻 Installation

```bash
cd Algorithmic/MatchingEngine
go build
go test
```

## 🚀 Usage

The `main` program accepts JSON commands.

**Input:**
```json
[
  {"type": "limit", "side": "sell", "price": 100, "quantity": 10, "id": 1},
  {"type": "limit", "side": "buy", "price": 100, "quantity": 5, "id": 2}
]
```

**Output:**
```json
[
  {"trades": []},
  {"trades": [{"buy_id": 2, "sell_id": 1, "price": 100, "quantity": 5}]}
]
```

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Add Limit Order** | $O(\log N)$ | $O(N)$ |
| **Match Order** | $O(M \log N)$ | $O(1)$ |

Where $N$ is number of orders in book, $M$ is number of matches generated.
