# Game Tree Search Framework

A generic framework for implementing game-playing AI using minimax algorithm with alpha-beta pruning and customizable evaluation functions.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

**Minimax** is a decision-making algorithm used in two-player zero-sum games. It assumes both players play optimally and looks ahead to find the best move.

### How It Works
1. **Game Tree**: Represent all possible game states as a tree
2. **Evaluation**: Assign scores to terminal states (win/loss/draw)
3. **Minimax Recursion**:
   - **Maximizing player** tries to maximize the score
   - **Minimizing player** tries to minimize the score
   - Alternate between players at each level

### Alpha-Beta Pruning
An optimization that eliminates branches that cannot affect the final decision:
- **Alpha**: Best score that the maximizer can guarantee
- **Beta**: Best score that the minimizer can guarantee
- **Prune** when $\alpha \geq \beta$

This can reduce search complexity from $O(b^d)$ to $O(b^{d/2})$ in the best case.

## 💻 Installation

Ensure you have Rust 1.70+ installed.

### Building the Library

```bash
cargo build --release
```

### Running Tests

```bash
cargo test
```

## 🚀 Usage

### Implementing a Game

```rust
use game_tree_search_framework::{GameState, GameTree};

// Implement the GameState trait for your game
impl GameState for TicTacToe {
    type Move = (usize, usize);
    
    fn get_legal_moves(&self) -> Vec<Self::Move> {
        // Return all legal moves
    }
    
    fn make_move(&mut self, m: &Self::Move) {
        // Apply the move
    }
    
    fn evaluate(&self) -> i32 {
        // Return game score from current player's perspective
    }
    
    fn is_terminal(&self) -> bool {
        // Check if game is over
    }
}

// Use the framework
let game = TicTacToe::new();
let depth = 9;  // Search to end of game
let best_move = GameTree::minimax_alpha_beta(&game, depth);
```

### Features
- Generic over game type
- Configurable search depth
- Alpha-beta pruning enabled by default
- Move ordering for better pruning
- Iterative deepening support

## 📊 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Minimax** | $O(b^d)$ | $O(d)$ |
| **Alpha-Beta** | $O(b^{d/2})$ (best case) | $O(d)$ |

Where:
- $b$ is the branching factor (average moves per position)
- $d$ is the search depth

**Example**: For Tic-Tac-Toe:
- $b \approx 5$, $d = 9$
- Minimax: ~2 million nodes
- Alpha-Beta: ~2,000 nodes (99% reduction)

## 🎬 Demos

### Running the Demo

```bash
cargo run --example tic_tac_toe
```

This demonstrates:
1. **Tic-Tac-Toe AI** that never loses
2. **Performance comparison** between minimax and alpha-beta
3. **Node counting** to show pruning efficiency
4. **Interactive play** against the AI

### Expected Output

```
AI thinking...
Nodes evaluated: 2,315
Best move: (1, 1)
Time: 0.003s
```

## Demos

To demonstrate the algorithm, run:

```bash
cargo run --release
```
