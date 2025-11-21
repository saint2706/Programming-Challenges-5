/// A trait representing a game state.
pub trait GameState: Clone + Sized {
    /// The type of move/action.
    type Action;
    /// The type of player identifier.
    type Player: Copy + PartialEq;

    /// Returns a list of legal moves from the current state.
    fn legal_moves(&self) -> Vec<Self::Action>;

    /// Applies a move to the state, returning a new state.
    fn apply(&self, action: &Self::Action) -> Self;

    /// Returns true if the game is over (terminal state).
    fn is_terminal(&self) -> bool;

    /// Returns the score of the state from the perspective of the maximizing player.
    /// Usually positive if maximizing player wins, negative if they lose.
    fn evaluate(&self, player: Self::Player) -> i32;

    /// Returns the player whose turn it is.
    fn current_player(&self) -> Self::Player;
}

/// A generic minimax solver with alpha-beta pruning.
pub struct MinimaxSolver;

impl MinimaxSolver {
    /// Finds the best move for the current player using minimax with alpha-beta pruning.
    /// `depth` is the maximum search depth.
    pub fn find_best_move<G: GameState>(state: &G, depth: u32) -> Option<G::Action> {
        let player = state.current_player();
        let moves = state.legal_moves();

        if moves.is_empty() {
            return None;
        }

        let mut best_move = None;
        let mut best_score = i32::MIN + 1; // Avoid overflow when negating MIN
        let alpha = i32::MIN + 1;
        let beta = i32::MAX;

        let mut current_alpha = alpha;

        for m in moves {
            let next_state = state.apply(&m);

            // When calling recursively, if the player changes, we negate the bounds and swap them.
            // alpha is the best we (current max) can guarantee.
            // beta is the best the opponent (min) can guarantee.
            // In recursive call for opponent:
            // new_alpha = -beta
            // new_beta = -current_alpha

            // Handle overflow if beta is MIN (shouldn't be, but good to be safe)
            let next_beta = if beta == i32::MIN { i32::MAX } else { -beta };
            let next_alpha = if current_alpha == i32::MIN { i32::MAX } else { -current_alpha };

            let next_player = next_state.current_player();
             let score = if next_player != player {
                 let recursive_val = Self::negamax(&next_state, depth - 1, next_beta, next_alpha, next_player);
                 if recursive_val == i32::MIN { i32::MAX } else { -recursive_val }
            } else {
                Self::negamax(&next_state, depth - 1, current_alpha, beta, player)
            };

            if score > best_score {
                best_score = score;
                best_move = Some(m);
            }

            if score > current_alpha {
                current_alpha = score;
            }
        }

        best_move
    }

    fn negamax<G: GameState>(state: &G, depth: u32, mut alpha: i32, beta: i32, player: G::Player) -> i32 {
        if depth == 0 || state.is_terminal() {
            return state.evaluate(player);
        }

        let moves = state.legal_moves();
        if moves.is_empty() {
             return state.evaluate(player);
        }

        let mut value = i32::MIN + 1;

        for m in moves {
            let next_state = state.apply(&m);
            let next_player = next_state.current_player();

            let score = if next_player != player {
                 let recursive_val = Self::negamax(&next_state, depth - 1, -beta, -alpha, next_player);
                 if recursive_val == i32::MIN { i32::MAX } else { -recursive_val }
            } else {
                Self::negamax(&next_state, depth - 1, alpha, beta, player)
            };

            value = value.max(score);
            alpha = alpha.max(value);
            if alpha >= beta {
                break;
            }
        }

        value
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Clone, Copy, PartialEq, Debug)]
    enum Player {
        X,
        O,
    }

    #[derive(Clone, Debug)]
    struct TicTacToe {
        board: [Option<Player>; 9],
        turn: Player,
    }

    impl TicTacToe {
        fn new() -> Self {
            TicTacToe {
                board: [None; 9],
                turn: Player::X,
            }
        }

        fn check_winner(&self) -> Option<Player> {
            const LINES: [[usize; 3]; 8] = [
                [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
                [0, 3, 6], [1, 4, 7], [2, 5, 8], // Cols
                [0, 4, 8], [2, 4, 6],            // Diags
            ];

            for line in LINES {
                if let Some(p) = self.board[line[0]] {
                    if self.board[line[1]] == Some(p) && self.board[line[2]] == Some(p) {
                        return Some(p);
                    }
                }
            }
            None
        }

        fn is_full(&self) -> bool {
            self.board.iter().all(|c| c.is_some())
        }
    }

    impl GameState for TicTacToe {
        type Action = usize;
        type Player = Player;

        fn legal_moves(&self) -> Vec<usize> {
            if self.check_winner().is_some() {
                return vec![];
            }
            self.board.iter().enumerate()
                .filter(|(_, c)| c.is_none())
                .map(|(i, _)| i)
                .collect()
        }

        fn apply(&self, action: &usize) -> Self {
            let mut new_state = self.clone();
            new_state.board[*action] = Some(self.turn);
            new_state.turn = match self.turn {
                Player::X => Player::O,
                Player::O => Player::X,
            };
            new_state
        }

        fn is_terminal(&self) -> bool {
            self.check_winner().is_some() || self.is_full()
        }

        fn evaluate(&self, player: Player) -> i32 {
            match self.check_winner() {
                Some(p) if p == player => 10,
                Some(_) => -10,
                None => 0,
            }
        }

        fn current_player(&self) -> Player {
            self.turn
        }
    }

    #[test]
    fn test_block_win() {
        let mut game = TicTacToe::new();
        game.board = [
            Some(Player::X), Some(Player::O), Some(Player::X),
            Some(Player::O), Some(Player::O), None,
            None, None, None
        ];
        game.turn = Player::X;

        let best_move = MinimaxSolver::find_best_move(&game, 5);
        assert_eq!(best_move, Some(5));
    }

    #[test]
    fn test_win_immediately() {
        let mut game = TicTacToe::new();
        game.board = [
            Some(Player::X), Some(Player::X), None,
            None, Some(Player::O), None,
            None, None, Some(Player::O)
        ];
        game.turn = Player::X;

        let best_move = MinimaxSolver::find_best_move(&game, 5);
        assert_eq!(best_move, Some(2));
    }
}
