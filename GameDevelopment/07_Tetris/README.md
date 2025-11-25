# Tetris with Ghost Piece & Hold

A full-featured Tetris implementation with ghost piece preview and hold functionality.

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)

## ✨ Features

- All 7 standard Tetrominoes (I, O, T, S, Z, J, L)
- Ghost piece showing where the piece will land
- Next piece preview
- Score tracking with level progression
- Line clear detection and animation
- SRS (Super Rotation System) wall kicks

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:
```bash
pip install pygame
```

## 🚀 Usage

### Running the Game
```bash
cd GameDevelopment/07_Tetris
python main.py
```

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Left/Right Arrow** | Move piece horizontally |
| **Down Arrow** | Soft drop |
| **Up Arrow** or **Space** | Hard drop |
| **Z** | Rotate counter-clockwise |
| **X** or **Up Arrow** | Rotate clockwise |
| **C** | Hold piece |
| **ESC** | Quit game |

## 🎯 Gameplay

- Arrange falling pieces to complete horizontal lines
- Completed lines are cleared and award points
- Game speed increases as you level up
- Game ends when pieces stack to the top
