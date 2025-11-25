# 2048 Variant

The classic 2048 sliding puzzle game with smooth animations.

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)

## ✨ Features

- 4x4 grid sliding mechanics
- Tile merging system
- Score tracking
- Game over detection
- Color-coded tiles based on value
- Clean, modern visual design

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:
```bash
pip install pygame
```

## 🚀 Usage

### Running the Game
```bash
cd GameDevelopment/08_2048
python main.py
```

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Arrow Keys** | Slide tiles in that direction |
| **R** | Restart game |
| **ESC/Close Window** | Quit game |

## 🎯 Gameplay

- Slide numbered tiles on a 4x4 grid
- When two tiles with the same number touch, they merge into one
- Create a tile with the number 2048 to win
- New tiles (2 or 4) spawn after each move
- Game ends when no more moves are possible
