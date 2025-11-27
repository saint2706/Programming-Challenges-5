# Simple RISC CPU Simulator

A cycle-accurate simulator for a 5-stage pipelined RISC processor (like MIPS).

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Pipelining
Instructions are broken into 5 stages:
1.  **IF**: Instruction Fetch
2.  **ID**: Instruction Decode / Register Read
3.  **EX**: Execute / ALU
4.  **MEM**: Memory Access
5.  **WB**: Write Back

Pipelining increases throughput (Instructions Per Cycle), but introduces hazards:
-   **Data Hazards**: Operands not ready (solved by forwarding or stalling).
-   **Control Hazards**: Branching (solved by prediction or flushing).

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DRISC_PIPELINE_DEMO main.cpp -o risc_cpu
./risc_cpu
```

## 📊 Complexity Analysis

-   **Throughput**: Ideally 1 instruction per cycle (IPC = 1).
-   **Simulation**: $O(I)$ where $I$ is the number of instructions.

## 🎬 Demos

The demo runs a sequence of instructions through the pipeline, printing the state of each stage (IF, ID, EX, MEM, WB) at every clock cycle.
