from __future__ import annotations

import math

from board import O, X, Board
from move import Move


class Player:
    def __init__(self, max_depth: int, player_letter: int) -> None:
        self.max_depth = max_depth  # how many moves ahead the player looks.
        self.player_letter = player_letter  # X (MAX) or O (MIN).
        self.visited_nodes = 0  # boards visited by the last search.

    def alpha_beta(self, board: Board) -> Move:
        """The best move for this player on the board, according to minimax with alpha-beta pruning."""
        self.visited_nodes = 0
        # no bounds yet: alpha starts at -infinity and beta at +infinity.
        if self.player_letter == X:
            return self.max_value_ab(board, 0, -math.inf, math.inf)
        return self.min_value_ab(board, 0, -math.inf, math.inf)

    def max_value_ab(self, board: Board, depth: int, alpha: float, beta: float) -> Move:
        """The best move for MAX (X) on the board, with its value; prunes with alpha and beta."""
        self.visited_nodes += 1
        if board.is_terminal() or depth == self.max_depth:
            return Move(board.last_move.row, board.last_move.col, board.evaluate())
        max_move = Move(value=-math.inf)

        children = board.get_children(X)
        if not children:
            return self.min_value_ab(board, depth, alpha, beta)
        for child in children:
            move = self.min_value_ab(child, depth + 1, alpha, beta)
            if move.value > max_move.value:
                max_move = Move(child.last_move.row, child.last_move.col, move.value)
            if max_move.value >= beta:
                return max_move
            alpha = max(alpha, max_move.value)
        return max_move

    def min_value_ab(self, board: Board, depth: int, alpha: float, beta: float) -> Move:
        """The best move for MIN (O) on the board, with its value; prunes with alpha and beta."""
        self.visited_nodes += 1
        if board.is_terminal() or depth == self.max_depth:
            return Move(board.last_move.row, board.last_move.col, board.evaluate())
        min_move = Move(value=math.inf)

        children = board.get_children(O)
        if not children:
            return self.max_value_ab(board, depth, alpha, beta)
        for child in children:
            move = self.max_value_ab(child, depth + 1, alpha, beta)
            if move.value < min_move.value:
                min_move = Move(child.last_move.row, child.last_move.col, move.value)
            if min_move.value <= alpha:
                return min_move
            beta = min(beta, min_move.value)
        return min_move
