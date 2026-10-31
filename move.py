from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Move:
    row: int = -1  # -1 means "no move", e.g. the last move of a new, empty board.
    col: int = -1
    value: float = 0  # the value of the move; a float, so that it can also be -inf or +inf.
