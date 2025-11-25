# Game Development Challenges - Plan

This directory contains solutions for the first 10 Game Development challenges from the repository's main README.

## Tech Stack
*   **Language:** Python 3
*   **Library:** `pygame` (Community Standard Edition) for graphical games.
*   **Exception:** Challenge #04 (Text Adventure) is a pure Python CLI application to better fit the genre.
*   **Assets:** All graphics are generated procedurally (drawing primitives) to keep the repository lightweight and self-contained.

## Directory Structure
Each challenge is contained in its own subdirectory with a `main.py`, `README.md`, and `requirements.txt`.

```text
GameDev/
├── 01_Snake/
├── 02_Breakout/
├── 03_Puzzle_Slider_15/
├── 04_Text_Adventure_Engine/ (CLI)
├── 05_Educational_Math_Game/
├── 06_Typing_Game/
├── 07_Tetris_Ghost_Hold/
├── 08_2048_Variant/
├── 09_Platformer_Prototype/
└── 10_TopDown_Shooter/
```

## Shared Utilities
While each game is designed to be self-contained (runnable via `python main.py` inside its folder), they share common architectural patterns:
*   **Game Loop:** Handle Input -> Update -> Draw -> Clock Tick.
*   **State Management:** Start Screen, Gameplay, Pause, Game Over.
*   **Colors:** Standard definition of colors (White, Black, Red, Green, Blue).

## Feature Summary

### 01. Snake with Polished UX
*   **Core:** Snake movement (deque), food spawning, self/wall collision.
*   **UX:** Start screen, Score HUD, Pause (P), Game Over with restart, High Score persistence (local file).

### 02. Breakout/Arkanoid Clone
*   **Core:** Paddle (mouse/keyboard), Ball physics (bounce off walls/paddle/bricks), Brick grid.
*   **UX:** Lives, Score, Win state (clear all bricks), Lose state.

### 03. Puzzle Slider Game (15-puzzle)
*   **Core:** 4x4 Grid, sliding tiles into the empty spot.
*   **Logic:** Shuffle algorithm ensuring solvability.
*   **UX:** Visual grid, click or arrow keys to move, Win check (sorted order).

### 04. Text Adventure Engine
*   **Core:** CLI loop. Data-driven rooms/items (dictionary/JSON structure).
*   **Logic:** Parser for commands ("go [dir]", "take [item]", "inventory").
*   **Content:** A mini-adventure sample.

### 05. Educational Math Game
*   **Core:** Generate arithmetic problems (`A op B = ?`).
*   **UX:** Text input for answer, visual feedback (correct/wrong), score tracking, difficulty scaling.

### 06. Typing Game
*   **Core:** Words falling from top. User types to eliminate them.
*   **UX:** Visual feedback on typed letters, Lives system (lose life if word hits bottom), Score.

### 07. Tetris with Ghost Piece & Hold
*   **Core:** Tetromino definitions (I, O, T, S, Z, J, L), Grid collision, Line clearing.
*   **UX:** "Ghost" piece showing drop location, Hold mechanism (swap piece), Next piece preview.

### 08. 2048 Variant
*   **Core:** 4x4 Grid, slide tiles (all move until stop), merge same values.
*   **UX:** Animations (simulated or simple frame steps), Score tracking, Win (2048)/Lose detection.

### 09. Platformer Prototype
*   **Core:** AABB Collision, Gravity, Jumping, Moving Platforms (optional), Hazards.
*   **UX:** Player rectangle, static level layout, "Goal" area.

### 10. Top-Down Shooter
*   **Core:** Top-down view, WASD movement, Mouse aim (rotation), Projectiles.
*   **Entities:** Player, Enemies (chase logic), Bullets.
*   **UX:** Health bars, Score, Waves or simple spawn logic.
