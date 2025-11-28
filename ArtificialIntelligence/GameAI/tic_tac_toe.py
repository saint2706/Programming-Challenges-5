"""Tic-Tac-Toe AI with minimax search.

Run this module directly to play against the AI in the terminal.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

Board = List[List[str]]

EMPTY = " "


def create_board() -> Board:
    return [[EMPTY for _ in range(3)] for _ in range(3)]


def print_board(board: Board) -> None:
    rows = [" | ".join(board[r]) for r in range(3)]
    separator = "\n---------\n"
    print("\n" + separator.join(rows) + "\n")


def check_winner(board: Board) -> Optional[str]:
    lines = []
    lines.extend(board)  # rows
    lines.extend([[board[r][c] for r in range(3)] for c in range(3)])  # columns
    lines.append([board[i][i] for i in range(3)])
    lines.append([board[i][2 - i] for i in range(3)])

    for line in lines:
        if line[0] != EMPTY and line.count(line[0]) == 3:
            return line[0]
    if all(cell != EMPTY for row in board for cell in row):
        return "draw"
    return None


def minimax(
    board: Board, player: str, maximizing: bool
) -> Tuple[int, Optional[Tuple[int, int]]]:
    winner = check_winner(board)
    if winner == player:
        return 1, None
    if winner == "draw":
        return 0, None
    if winner is not None:
        return -1, None

    best_score = float("-inf") if maximizing else float("inf")
    best_move: Optional[Tuple[int, int]] = None
    opponent = "O" if player == "X" else "X"

    current_player = player if maximizing else opponent

    for r in range(3):
        for c in range(3):
            if board[r][c] == EMPTY:
                board[r][c] = current_player
                score, _ = minimax(board, player, not maximizing)
                board[r][c] = EMPTY

                if maximizing:
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
                else:
                    if score < best_score:
                        best_score = score
                        best_move = (r, c)

    return best_score, best_move


def best_move(board: Board, player: str) -> Tuple[int, int]:
    """Return the best move for `player` using minimax."""
    _, move = minimax(board, player, True)
    if move is None:
        raise ValueError("No moves available")
    return move


def human_turn(board: Board) -> None:
    while True:
        try:
            raw = input("Enter your move as row,col (1-3): ")
            row_str, col_str = raw.split(",")
            r, c = int(row_str) - 1, int(col_str) - 1
            if 0 <= r < 3 and 0 <= c < 3 and board[r][c] == EMPTY:
                board[r][c] = "O"
                return
        except ValueError:
            pass
        print("Invalid move. Try again.")


def ai_turn(board: Board) -> None:
    r, c = best_move(board, "X")
    board[r][c] = "X"


def play_game() -> None:
    print("You are O. AI is X. AI goes first.\n")
    board = create_board()
    while True:
        ai_turn(board)
        winner = check_winner(board)
        print_board(board)
        if winner:
            break

        human_turn(board)
        winner = check_winner(board)
        print_board(board)
        if winner:
            break

    if winner == "draw":
        print("It's a draw!")
    else:
        print(f"{winner} wins!")


if __name__ == "__main__":
    play_game()
