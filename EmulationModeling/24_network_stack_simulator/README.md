# Network Stack Simulator

A simulation of a simplified TCP/IP network stack, modeling the flow of data through layers (Application, Transport, Network, Link).

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Encapsulation

Data travels down the stack, getting wrapped in headers at each layer.

1.  **Application**: Raw data ("Hello").
2.  **Transport (TCP)**: Adds Ports/Seq numbers.
3.  **Network (IP)**: Adds Source/Dest IP.
4.  **Link (Ethernet)**: Adds MAC addresses.

### Decapsulation

The receiving side strips headers layer by layer to retrieve the original data.

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DNETWORK_STACK_DEMO main.cpp -o net_stack
./net_stack
```

## 📊 Complexity Analysis

- **Encapsulate/Decapsulate**: $O(L)$ where $L$ is the number of layers (constant 4 here).
- **Data Copying**: $O(D)$ where $D$ is the data size.

## 🎬 Demos

The demo simulates a client sending an HTTP-like request. It prints the packet structure at each layer:
`[MAC] [IP] [TCP] [APP] payload`
