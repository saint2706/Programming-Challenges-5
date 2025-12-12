# Turn-Based Strategy Microgame

A grid-based tactical game where you command a unit against AI-controlled enemies in turn-based combat.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)
- [Gameplay](#gameplay)

## ✨ Features

- **Grid-Based Tactical Combat**: 10x10 tile grid for strategic positioning
- **Turn-Based Gameplay**: Alternating turns between player and AI
- **Unit Management**: Units with HP, movement range, and attack range
- **Simple AI**: Enemies move towards player and attack when in range
- **Visual Feedback**: Highlighted valid moves and attack targets
- **Combat System**: Attack damage, HP tracking, and unit elimination
- **Victory/Defeat Conditions**: Eliminate all enemies to win

## 💻 Installation

Ensure you have Python 3.8+ and pygame installed:

```bash
pip install pygame
```

## 🚀 Usage

### Running the Game

```bash
cd GameDevelopment/11_TurnBasedStrategy
python main.py
```

## 🎮 Controls

| Action          | Control                          |
| :-------------- | :------------------------------- |
| **Select Unit** | Left click on your unit          |
| **Move**        | Left click on green tile         |
| **Attack**      | Left click on orange tile        |
| **End Turn**    | Click "End Turn" button or SPACE |
| **Restart**     | R (when game over)               |
| **Quit**        | ESC                              |

## 🎯 Gameplay

### Objective

Eliminate all enemy units while keeping your unit alive.

### Mechanics

1. **Your Turn**:
   - Click on your unit (blue circle) to select it
   - Green tiles show where you can move (within movement range)
   - Orange tiles show enemies you can attack (within attack range)
   - Click a green tile to move
   - Click an orange tile to attack
   - You can move and attack in any order during your turn
   - Click "End Turn" when you're done

2. **Enemy Turn**:
   - AI enemies will automatically move towards you
   - If you're in their attack range, they'll attack
   - Each enemy gets to act once per turn

3. **Combat**:
   - Each attack deals 30 damage
   - Units have 100 HP
   - HP bars are shown below each unit (green = healthy, orange = damaged, red = critical)
   - Units are eliminated when HP reaches 0

4. **Victory/Defeat**:
   - **Victory**: Eliminate all enemy units
   - **Defeat**: Your unit's HP reaches 0
   - Press R to restart

### Strategy Tips

- Use your movement range to maintain distance from enemies
- Attack enemies before they get too close
- Position yourself to avoid being surrounded
- Watch your HP and enemy HP bars
- Plan your moves carefully - once you end your turn, enemies will act
