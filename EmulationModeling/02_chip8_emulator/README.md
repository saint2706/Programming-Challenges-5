# Chip-8 Emulator

A complete Chip-8 interpreter implementing all 35 opcodes with display, keypad input, and timer support.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)

## 🧠 Theory

### Chip-8 System

Chip-8 is an interpreted programming language from the 1970s designed for simple game development:

- **Memory**: 4KB RAM (0x000-0xFFF)
- **Display**: 64x32 monochrome pixels
- **Registers**: 16 8-bit registers (V0-VF)
- **Stack**: 16 levels for subroutine calls
- **Timers**: 60Hz delay and sound timers
- **Keypad**: 16-key hexadecimal input

### Instruction Cycle

1. **Fetch**: Read 2-byte opcode from memory at PC
2. **Decode**: Parse opcode to determine instruction
3. **Execute**: Perform operation (arithmetic, graphics, control flow)
4. **Update**: Increment PC, update timers

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:

```bash
pip install pygame
```

## 🚀 Usage

### Running a ROM

```bash
cd EmulationModeling/02_chip8_emulator
python main.py path/to/rom.ch8
```

### Running Test ROM

Without a ROM file, runs internal test that displays a sprite:

```bash
python main.py
```

## 🏗 Architecture

### Components

- **CPU** (`cpu.py`): Executes instructions, manages registers and memory
- **Display** (`display.py`): Renders 64x32 pixel graphics using pygame
- **Keypad** (`keypad.py`): Maps keyboard input to Chip-8's 16-key layout

### Keypad Mapping

```
Chip-8          Keyboard
1 2 3 C    →    1 2 3 4
4 5 6 D    →    Q W E R
7 8 9 E    →    A S D F
A 0 B F    →    Z X C V
```

### Clock Speed

- CPU runs at ~600 Hz (10 cycles per frame at 60 FPS)
- Timers decrement at 60 Hz
