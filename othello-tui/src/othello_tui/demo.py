"""Static game data for the interface.
The opening position is the classic one: four discs in the middle of the grid,
two black and two white, each colour sitting on one of the two diagonals of
the central 2x2 block.
"""

from __future__ import annotations

from typing import Final

#: Width and height of the board, in cells.
BOARD_SIZE: Final = 8

#: Contents of a square.
EMPTY: Final = "."
BLACK: Final = "B"
WHITE: Final = "W"

#: Column letters used by the coordinate labels ("a1" at the top left).
COLUMN_LABELS: Final = "abcdefgh"

#: -- Game state at the start of a game --------------------------------------

START_ROUND: Final = 1
#: A game of Othello lasts at most 60 rounds (60 empty squares at the start).
TOTAL_ROUNDS: Final = 60 # display-only.
START_TURN: Final = BLACK

#: Where the keyboard cursor starts, as a (row, column) pair.
START_CURSOR: Final[tuple[int, int]] = (2, 3)

#: -- Opening position -------------------------------------------------------

#: The central 2x2 block: white on d4/e5, black on e4/d5 (Othello notation,
#: a1 is the top left square).  One string per row, "B"lack / "W"hite / ".".
START_BOARD: Final[list[str]] = [
    "........",
    "........",
    "........",
    "...WB...",
    "...BW...",
    "........",
    "........",
    "........",
]

HUMAN: Final = BLACK
AI: Final = WHITE
# AI_DEPTH: Final = 4




def cell_label(row: int, col: int) -> str:
    """Coordinate label of a square, e.g. ``d3`` for row 2, column 3."""
    return f"{COLUMN_LABELS[col]}{row + 1}"


def piece_name(piece: str) -> str:
    """Display name of a square's content."""
    return {EMPTY: "Empty", BLACK: "Black", WHITE: "White"}[piece]


def count_discs(board: list[list[str]], piece: str) -> int:
    """Number of discs of a colour on a board (for the score display)."""
    return sum(row.count(piece) for row in board)
