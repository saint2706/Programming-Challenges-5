# Puzzle Slider Game (15-puzzle)

A classic 15-puzzle implementation in Python using Pygame.

## Features
- **Logic:** 4x4 Grid with one empty space.
- **Controls:** Click tiles or use Arrow keys to move tiles into the empty space.
- **Solvability:** Shuffle algorithm ensures the puzzle is always solvable.
- **Win Condition:** Automatically detects when tiles are in order (1-15).

## How to Run

1.  Ensure you have Python installed.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the game:
    ```bash
    python main.py
    ```

## Controls
- **Arrow Keys:** Move the empty space (e.g., UP moves the tile below the empty space UP).
- **Mouse:** Click a tile adjacent to the empty space to move it.
- **R:** Shuffle / Restart
- **Esc:** Quit
