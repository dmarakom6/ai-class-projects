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

        # fill in your code here! Remember: if X has no valid move here, X passes and O plays on the same board.
        a = alpha
        for child in board.get_children(X):
            move = self.min_value_ab(child,depth+1,a,beta)
            if ( move.score > max_move.score):
                max_move = move
            if( max_move.score >= beta):
                return max_move
            a = max(max_move.score,alpha)
        return max_move

    def min_value_ab(self, board: Board, depth: int, alpha: float, beta: float) -> Move:
        """The best move for MIN (O) on the board, with its value; prunes with alpha and beta."""
        self.visited_nodes += 1
        if board.is_terminal() or depth == self.max_depth:
            return Move(board.last_move.row, board.last_move.col, board.evaluate())
        min_move = Move(value=math.inf)

        # fill in your code here! Remember: if O has no valid move here, O passes and X plays on the same board.
        b = beta
        for child in board.get_children(O):
            move = self.max_value_ab(child,depth+1,alpha,b)
            if ( move.score < min_move.score):
                min_move = move
            if( min_move.score <= alpha):
                return min_move
            b = min(min_move,beta)
        return min_move
