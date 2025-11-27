# Classic Game AI (Tic-Tac-Toe & Connect-4)

## Overview
This project implements AI agents for classic board games like Tic-Tac-Toe and Connect-4 using the Minimax algorithm.

## Features
- **Tic-Tac-Toe:** Unbeatable AI using standard Minimax.
- **Connect-4:** AI using Minimax with Alpha-Beta pruning for efficiency.
- Interactive CLI for playing against the AI.

## Installation
1.  Navigate to the project directory:
    ```bash
    cd ArtificialIntelligence/GameAI
    ```
2.  Install dependencies (if any):
    ```bash
    # No external dependencies required
    ```

## Usage
Run the Tic-Tac-Toe game:
```bash
python tic_tac_toe.py
```

Run the Connect-4 game:
```bash
python connect_four.py
```

## Implementation Details
- **Minimax:** Recursive algorithm that evaluates all possible future moves to find the optimal strategy.
- **Alpha-Beta Pruning:** Optimization that stops evaluating a move when at least one possibility has been found that proves the move to be worse than a previously examined move.

## Future Improvements
- Add a GUI using Pygame.
- Implement more advanced heuristics for Connect-4.
