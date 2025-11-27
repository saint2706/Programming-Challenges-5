# Multiplayer Network Lag Simulator

A tool to simulate network conditions such as latency, jitter, and packet loss for testing multiplayer game synchronization.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Network Imperfections
Real-world networks are not perfect.
-   **Latency (Ping)**: Time taken for data to travel.
-   **Jitter**: Variation in latency.
-   **Packet Loss**: Data that never arrives.
-   **Reordering**: Packets arriving in the wrong order.

### Simulation
The simulator uses a priority queue to schedule packet delivery based on `arrival_time = now + latency + jitter`. It randomly drops packets based on a configured probability.

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DLAG_SIMULATOR_DEMO main.cpp -o lag_sim
./lag_sim
```

### API
```cpp
// Config: 100ms lag, 20ms jitter, 10% loss
NetworkSimulator net(0.1, 0.02, 0.1);

net.send_packet("Player moved", 0.0);

// In game loop
auto packets = net.receive_packets(current_time);
```

## 📊 Complexity Analysis

| Operation | Complexity | Description |
| :--- | :--- | :--- |
| **Send** | $O(\log P)$ | Pushing to priority queue ($P$ pending packets). |
| **Receive** | $O(K \log P)$ | Popping $K$ ready packets. |

## 🎬 Demos

The demo sends numbered packets with timestamps and prints when they are received (or if they were lost), showing the effect of simulated lag.
