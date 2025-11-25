# Breakout/Arkanoid Clone

A classic brick-breaking game where you bounce a ball off a paddle to destroy bricks.

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)

## ✨ Features

- Paddle-controlled ball bouncing
- Multiple rows of colored bricks
- Score tracking
- Ball physics with angle-based bouncing
- AABB collision detection

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:
```bash
pip install pygame
```

## 🚀 Usage

### Running the Game
```bash
cd GameDevelopment/02_Breakout
python main.py
```

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Left/Right Arrow Keys** or **A/D** | Move paddle |
| **Space** | Launch ball (if applicable) |
| **ESC/Close Window** | Quit game |

## 🎯 Gameplay

- Move the paddle to bounce the ball
- Destroy all bricks to win
- Don't let the ball fall below the paddle
