"""Connect 4 AI with alpha-beta pruning.

Run this module directly to play against the AI in the terminal.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

ROWS, COLS = 6, 7
EMPTY = " "
Board = List[List[str]]


def create_board() -> Board:
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def print_board(board: Board) -> None:
    for row in board:
        print("|" + "|".join(row) + "|")
    print(" " + " ".join(str(i + 1) for i in range(COLS)))


def drop_piece(board: Board, col: int, piece: str) -> Optional[int]:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = piece
            return r
    return None


def valid_moves(board: Board) -> List[int]:
    return [c for c in range(COLS) if board[0][c] == EMPTY]


def check_winner(board: Board, last_row: int, last_col: int) -> Optional[str]:
    piece = board[last_row][last_col]
    if piece == EMPTY:
        return None

    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for sign in (1, -1):
            r, c = last_row, last_col
            while True:
                r += dr * sign
                c += dc * sign
                if 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == piece:
                    count += 1
                else:
                    break
        if count >= 4:
            return piece
    if all(board[0][c] != EMPTY for c in range(COLS)):
        return "draw"
    return None


def score_window(window: List[str], piece: str) -> int:
    opponent = "O" if piece == "X" else "X"
    score = 0
    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2
    if window.count(opponent) == 3 and window.count(EMPTY) == 1:
        score -= 4
    return score


def heuristic(board: Board, piece: str) -> int:
    score = 0
    # Center preference
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_col.count(piece) * 3

    # Horizontal
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS - 3):
            window = row[c : c + 4]
            score += score_window(window, piece)

    # Vertical
    for c in range(COLS):
        col = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col[r : r + 4]
            score += score_window(window, piece)

    # Diagonals
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window, piece)
            window = [board[r + 3 - i][c + i] for i in range(4)]
            score += score_window(window, piece)

    return score


def alpha_beta(
    board: Board,
    depth: int,
    alpha: int,
    beta: int,
    maximizing: bool,
    player: str,
    last_move: Optional[Tuple[int, int]],
) -> Tuple[int, Optional[int]]:
    if last_move is not None:
        winner = check_winner(board, *last_move)
        if winner == player:
            return 10_000, None
        if winner and winner != player:
            return -10_000, None
        if winner == "draw":
            return 0, None
    if depth == 0:
        return heuristic(board, player), None

    valid = valid_moves(board)
    if not valid:
        return 0, None

    opponent = "O" if player == "X" else "X"

    if maximizing:
        value = -float("inf")
        best_col: Optional[int] = None
        for col in valid:
            row = drop_piece(board, col, player)
            if row is None:
                continue
            score, _ = alpha_beta(
                board, depth - 1, alpha, beta, False, player, (row, col)
            )
            board[row][col] = EMPTY
            if score > value:
                value = score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_col

    value = float("inf")
    best_col = None
    for col in valid:
        row = drop_piece(board, col, opponent)
        if row is None:
            continue
        score, _ = alpha_beta(board, depth - 1, alpha, beta, True, player, (row, col))
        board[row][col] = EMPTY
        if score < value:
            value = score
            best_col = col
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value, best_col


def best_move(board: Board, player: str, depth: int = 4) -> int:
    """Return the best column for `player` using alpha-beta pruning."""
    _, col = alpha_beta(board, depth, -float("inf"), float("inf"), True, player, None)
    if col is None:
        raise ValueError("No moves available")
    return col


def human_turn(board: Board) -> Tuple[int, int]:
    while True:
        try:
            col = int(input("Choose a column (1-7): ")) - 1
            if 0 <= col < COLS and board[0][col] == EMPTY:
                row = drop_piece(board, col, "O")
                if row is not None:
                    return row, col
        except ValueError:
            pass
        print("Invalid move. Try again.")


def ai_turn(board: Board) -> Tuple[int, int]:
    col = best_move(board, "X")
    row = drop_piece(board, col, "X")
    if row is None:
        raise RuntimeError("AI attempted an invalid move")
    return row, col


def play_game() -> None:
    print("You are O. AI is X. AI goes first.\n")
    board = create_board()
    last_move: Optional[Tuple[int, int]] = None
    while True:
        last_move = ai_turn(board)
        winner = check_winner(board, *last_move)
        print_board(board)
        if winner:
            break

        last_move = human_turn(board)
        winner = check_winner(board, *last_move)
        print_board(board)
        if winner:
            break

    if winner == "draw":
        print("It's a draw!")
    else:
        print(f"{winner} wins!")


if __name__ == "__main__":
    play_game()
