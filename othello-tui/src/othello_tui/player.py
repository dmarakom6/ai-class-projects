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
        """The best move for this player on the board, according to minimax with alpha-beta pruning.

        Returns Move(-1, -1) when this player has no legal move and must pass: no move exists, and
        the caller must not play anything - a pass is not a move. Call this only on this player's
        turn: a search always answers for self.player_letter, never for whoever is to move."""
        self.visited_nodes = 0
        # no bounds yet: alpha starts at -infinity and beta at +infinity.
        if self.player_letter == X:
            return self.max_value_ab(board, 0, -math.inf, math.inf)
        return self.min_value_ab(board, 0, -math.inf, math.inf)

    def max_value_ab(self, board: Board, depth: int, alpha: float, beta: float) -> Move:
        """The best move for MAX (X) on the board, with its value; prunes with alpha and beta."""
        self.visited_nodes += 1
        # a leaf of the search: score the position instead of searching deeper
        if board.is_terminal() or depth == self.max_depth:
            return Move(board.last_move.row, board.last_move.col, board.evaluate())
        max_move = Move(value=-math.inf)

        children = board.get_children(X)
        if not children:
            # X must pass: O plays on the same board, so no ply is spent. The value is O's best
            # play, but the coordinates stay (-1, -1), "no move": the caller must never mistake
            # O's move for X's - playing it as X is what corrupts the game.
            passed = self.min_value_ab(board, depth, alpha, beta)
            return Move(-1, -1, passed.value)
        for child in children:
            move = self.min_value_ab(child, depth + 1, alpha, beta)
            if move.value > max_move.value:
                # carry the coordinates of our own move into the chosen child, with its backed-up value
                max_move = Move(child.last_move.row, child.last_move.col, move.value)
            if max_move.value >= beta:
                # MIN would never allow this line: searching the rest cannot change the choice
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
            # O must pass: X plays on the same board. Same contract as in max_value_ab: the value
            # is X's best play, the coordinates stay (-1, -1), "no move".
            passed = self.max_value_ab(board, depth, alpha, beta)
            return Move(-1, -1, passed.value) # This fixes a bug where if the player has no valid moves to make, he makes a move with the opponent's chosen coords!
        for child in children:
            move = self.max_value_ab(child, depth + 1, alpha, beta)
            if move.value < min_move.value:
                min_move = Move(child.last_move.row, child.last_move.col, move.value)
            if min_move.value <= alpha:
                # MAX would never allow this line: prune the rest
                return min_move
            beta = min(beta, min_move.value)
        return min_move
