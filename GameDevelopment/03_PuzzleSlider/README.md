# Puzzle Slider Game (15-puzzle)

A classic sliding puzzle game where you arrange numbered tiles in order.

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)

## ✨ Features

- 4x4 grid sliding puzzle
- Shuffle functionality
- Win condition detection
- Visual tile rendering
- Move validation (only adjacent tiles can slide)

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:
```bash
pip install pygame
```

## 🚀 Usage

### Running the Game
```bash
cd GameDevelopment/03_PuzzleSlider
python main.py
```

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Mouse Click** | Slide a tile into the empty space |
| **R** | Reshuffle the puzzle |
| **ESC/Close Window** | Quit game |

## 🎯 Gameplay

- Click on tiles adjacent to the empty space to slide them
- Arrange all tiles in numerical order (1-15)
- The empty space should end up in the bottom-right corner
