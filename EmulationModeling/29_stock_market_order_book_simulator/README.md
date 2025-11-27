# Stock Market Order Book Simulator

A financial exchange matching engine that handles limit orders, market orders, and order cancellations.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### The Order Book
Maintains two sides:
-   **Bids**: Buy orders, sorted high-to-low.
-   **Asks**: Sell orders, sorted low-to-high.

### Price-Time Priority
Orders are matched primarily by best price. If prices are equal, the order that arrived first is matched first (FIFO).

### Matching Logic
1.  **Incoming Buy**: Check against lowest Ask. If Bid Price $\ge$ Ask Price, trade occurs.
2.  **Incoming Sell**: Check against highest Bid. If Ask Price $\le$ Bid Price, trade occurs.

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DORDER_BOOK_DEMO main.cpp -o order_book
./order_book
```

### API
```cpp
OrderBook book;
book.add_order({1, Side::BUY, 100, 10});  // Buy 10 @ $100
book.add_order({2, Side::SELL, 100, 5});  // Sell 5 @ $100 -> Trade occurs
```

## 📊 Complexity Analysis

| Operation | Complexity | Description |
| :--- | :--- | :--- |
| **Add Order (No Match)** | $O(\log N)$ | Insertion into map (balanced tree). |
| **Match Order** | $O(M \cdot \log N)$ | Processing $M$ matches against resting orders. |
| **Cancel Order** | $O(1)$ amortized | Using a hash map index to find the order. |

## 🎬 Demos

The demo adds buy and sell orders that cross, printing the resulting trades and quantities.
