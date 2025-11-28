# Game Boy Emulator Core

A simplified, educational emulation core for the Sharp LR35902 CPU (Game Boy).

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### CPU Architecture

The Game Boy CPU is an 8-bit processor similar to the Zilog Z80 and Intel 8080.

- **Registers**: A, B, C, D, E, H, L (8-bit) and PC, SP (16-bit).
- **Flags**: Zero (Z), Subtract (N), Half-Carry (H), Carry (C).
- **Memory**: 16-bit address bus (64KB addressable space).

### Fetch-Decode-Execute Cycle

1.  **Fetch**: Read the byte at the Program Counter (PC).
2.  **Decode**: Determine the instruction (opcode).
3.  **Execute**: Perform the operation (ALU, Load/Store, Jump) and update cycles/flags.

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DGAMEBOY_CORE_DEMO main.cpp -o gb_core
./gb_core
```

### API

```cpp
MiniGameBoy cpu;
std::vector<uint8_t> program = { 0x3E, 0x05, 0x76 }; // LD A, 5; HALT
cpu.load_program(program);

while (!cpu.is_halted()) {
    cpu.step();
}
```

## 📊 Complexity Analysis

- **Step**: $O(1)$ constant time per instruction.
- **Memory Access**: $O(1)$ array access.

## 🎬 Demos

The demo runs a small assembly program:

```asm
LD A, 5
LD B, 3
ADD A, B  ; A = 8
JR NZ, +2 ; Jump if Not Zero
...
```

Output:

```text
Register A: 8
Memory[0xBFFF]: 0
```
