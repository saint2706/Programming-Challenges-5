"""Negamax bot for the grid games in :mod:`boardgames`.

The search is a negamax with alpha-beta pruning, iterative deepening, a
transposition table (with bound flags, so cached values stay sound) and
centre-first move ordering. Because both games are *n-in-a-row*, one evaluation
function covers them: score the windows each side could still complete,
weighted by how many marks are already in them.

On a 3x3 Tic-Tac-Toe board the tree is small enough that ``Difficulty.HARD``
searches it exhaustively and therefore plays perfectly — it never loses. On a
Connect Four board the depth and time limits do the work instead.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum

from boardgames import GridGame, Mark

#: Score of a win at ply 0. Wins found deeper score slightly lower, so the bot
#: prefers the quickest win and the most drawn-out loss.
WIN_SCORE = 1_000_000
#: Sentinel wider than any real score, used as +/- infinity.
INF = WIN_SCORE * 2

# Transposition table entry flags.
_EXACT = 0
_LOWER = 1
_UPPER = 2


class Difficulty(str, Enum):
    """Preset search budgets exposed to both front-ends."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class BotConfig:
    """Search budget and randomness for a difficulty level."""

    max_depth: int
    time_limit: float
    #: Probability of ignoring the search and playing a random legal move.
    blunder_rate: float = 0.0


BOT_CONFIGS: dict[Difficulty, BotConfig] = {
    Difficulty.EASY: BotConfig(max_depth=2, time_limit=0.05, blunder_rate=0.35),
    Difficulty.MEDIUM: BotConfig(max_depth=5, time_limit=0.4),
    Difficulty.HARD: BotConfig(max_depth=64, time_limit=2.5),
}


class _SearchTimeout(Exception):
    """Raised internally to abandon an iteration that ran out of time."""


class Bot:
    """A negamax player.

    Parameters
    ----------
    difficulty:
        Preset budget; ignored when ``config`` is given.
    config:
        Explicit :class:`BotConfig`, useful for deterministic tests.
    rng:
        Random source for tie-breaking and blunders. Pass a seeded
        ``random.Random`` to make the bot reproducible.
    """

    def __init__(
        self,
        difficulty: Difficulty | str = Difficulty.MEDIUM,
        config: BotConfig | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.difficulty = Difficulty(difficulty)
        self.config = config or BOT_CONFIGS[self.difficulty]
        self.rng = rng or random.Random()
        #: Nodes visited by the most recent :meth:`choose` call.
        self.nodes = 0
        #: Deepest iteration completed by the most recent :meth:`choose` call.
        self.depth_reached = 0
        self._table: dict[tuple, tuple[int, int, int]] = {}
        self._deadline = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def choose(self, game: GridGame) -> int:
        """Return the move the bot wants to play in ``game``.

        ``game`` itself is never mutated: the search runs on a copy.
        """
        moves = game.legal_moves()
        if not moves:
            raise ValueError("no legal moves available")
        if len(moves) == 1:
            return moves[0]
        if self.config.blunder_rate and self.rng.random() < self.config.blunder_rate:
            return self.rng.choice(moves)

        board = game.copy()
        self.nodes = 0
        self.depth_reached = 0
        self._table.clear()
        self._deadline = time.monotonic() + self.config.time_limit

        best_move = self._ordered_moves(board)[0]
        # A forced result cannot score closer to zero than this.
        decisive = WIN_SCORE - board.rows * board.cols
        max_depth = min(self.config.max_depth, board.empty_count)
        for depth in range(1, max_depth + 1):
            try:
                move, score = self._search_root(board, depth)
            except _SearchTimeout:
                break
            best_move = move
            self.depth_reached = depth
            if abs(score) >= decisive:
                # Win or loss proven; a deeper search cannot change the verdict.
                break
        return best_move

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def _search_root(self, board: GridGame, depth: int) -> tuple[int, int]:
        """Search every root move to ``depth`` and return ``(move, score)``.

        Each child is searched with ``beta = +INF`` and ``alpha`` one below the
        best score so far. That keeps alpha-beta pruning inside the subtrees
        while guaranteeing any move that *matches* the best score gets an exact
        value back — so tie-breaking never picks up a move whose real value is
        worse.
        """
        best_score = -INF
        best_moves: list[int] = []
        for move in self._ordered_moves(board):
            board.play(move)
            try:
                score = -self._negamax(board, depth - 1, -INF, -(best_score - 1))
            finally:
                board.undo()
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        return self.rng.choice(best_moves), best_score

    def _negamax(self, board: GridGame, depth: int, alpha: int, beta: int) -> int:
        self.nodes += 1
        if self.nodes % 4096 == 0 and time.monotonic() > self._deadline:
            raise _SearchTimeout

        if board.winner is not None:
            # The side to move has just been beaten.
            return -(WIN_SCORE - len(board.history))
        moves = board.legal_moves()
        if not moves:
            return 0
        if depth <= 0:
            return self._evaluate(board)

        alpha_original = alpha
        key = board.position_key()
        cached = self._table.get(key)
        if cached is not None:
            value, cached_depth, flag = cached
            if cached_depth >= depth:
                if flag == _EXACT:
                    return value
                if flag == _LOWER:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        best = -INF
        for move in self._ordered_moves(board, moves):
            board.play(move)
            try:
                score = -self._negamax(board, depth - 1, -beta, -alpha)
            finally:
                board.undo()
            best = max(best, score)
            alpha = max(alpha, best)
            if alpha >= beta:
                break

        if best <= alpha_original:
            flag = _UPPER
        elif best >= beta:
            flag = _LOWER
        else:
            flag = _EXACT
        previous = self._table.get(key)
        if previous is None or previous[1] <= depth:
            self._table[key] = (best, depth, flag)
        return best

    def _ordered_moves(
        self, board: GridGame, moves: list[int] | None = None
    ) -> list[int]:
        """Legal moves sorted by how central their landing cell is."""
        moves = board.legal_moves() if moves is None else moves
        centre_row = (board.rows - 1) / 2
        centre_col = (board.cols - 1) / 2

        def distance(move: int) -> float:
            row, col = board.coords(board.cell_for_move(move))
            return abs(row - centre_row) + abs(col - centre_col)

        return sorted(moves, key=distance)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def _evaluate(self, board: GridGame) -> int:
        """Heuristic score of ``board`` from the perspective of the mover."""
        mover = board.turn
        return self._side_score(board, mover) - self._side_score(board, mover.other)

    @staticmethod
    def _side_score(board: GridGame, mark: Mark) -> int:
        """Weighted count of the windows ``mark`` can still complete."""
        total = 0
        for window in board.open_windows(mark):
            filled = sum(1 for cell in window if board.cells[cell] is mark)
            if filled:
                # Near-complete windows are worth exponentially more.
                total += 10 ** (filled - 1)
        return total


def best_move(
    game: GridGame,
    difficulty: Difficulty | str = Difficulty.MEDIUM,
    seed: int | None = None,
) -> int:
    """Convenience wrapper: build a :class:`Bot` and pick a single move."""
    rng = random.Random(seed) if seed is not None else None
    return Bot(difficulty, rng=rng).choose(game)
