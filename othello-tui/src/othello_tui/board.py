from __future__ import annotations

from move import Move

Grid = list[list[int]]

BOARD_SIZE = 8  # Othello is played on an 8 x 8 board.

# What a square can hold: a piece of X, a piece of O, or nothing. The letters are numbers,
# so that the opponent of a player is simply -letter.
X = 1  # X plays first (the dark pieces of Othello).
O = -1
EMPTY = 0
SYMBOLS = {X: "X", O: "O", EMPTY: "-"}


def starting_grid() -> Grid:
    """The starting position of Othello: four pieces in the centre, each player's two on a diagonal."""
    grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    middle = BOARD_SIZE // 2
    grid[middle - 1][middle - 1] = grid[middle][middle] = O
    grid[middle - 1][middle] = grid[middle][middle - 1] = X
    return grid


class Board:
    def __init__(self, game_board: Grid | None = None, last_player: int = O) -> None:
        if game_board is None:
            game_board = starting_grid()
        # very important: keep our own copy of the grid, so that playing on a child never changes its parent.
        self.game_board = [row[:] for row in game_board]
        # who played last, i.e. whose move resulted in this board. Even a new board has one: it tells us
        # who plays first. A new board says that O played last, so X plays first.
        self.last_player = last_player
        # the move that led to this board (no move yet for a new board).
        self.last_move = Move()

    def copy(self) -> Board:
        board = Board(self.game_board, self.last_player)
        board.last_move = self.last_move
        return board

    def __str__(self) -> str:
        # each row is "* " + BOARD_SIZE symbols with spaces between them + " *", so 2 * BOARD_SIZE + 3 characters.
        border = "*" * (2 * BOARD_SIZE + 3)
        rows = ("* " + " ".join(SYMBOLS[cell] for cell in row) + " *" for row in self.game_board)
        return "\n".join([border, *rows, border])

    def make_move(self, row: int, col: int, letter: int) -> None:
        """Place a piece of letter at (row, col), flip the opponent's pieces it outflanks, remember the move."""
        # a square off the board means a bug, e.g. playing Move(-1, -1) when there was no valid move: that
        # player must pass instead. Without this check, Python's negative indices would fill a wrong square.
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise ValueError(f"({row}, {col}) is not on the board; a player with no valid move must pass.")
        self.game_board[row][col] = letter

        # fill in your code here! flip the opponent's pieces that the new piece outflanks.
        self.last_move = Move(row, col)
        self.last_player = letter

    def is_valid_move(self, row: int, col: int, letter: int) -> bool:
        """True if letter may play at (row, col): the square is empty and the move outflanks opponent pieces."""
        is_valid = False

        # fill in your code here!
        return is_valid

    def get_children(self, letter: int) -> list[Board]:
        """One child board for every valid move of letter."""
        children = []

        # fill in your code here!
        return children

    def evaluate(self) -> int:
        """The heuristic value of the board: positive is good for X (MAX), negative is good for O (MIN)."""
        score = 0

        # fill in your code here!
        return score

    def is_terminal(self) -> bool:
        """The game is over when neither player has a valid move (for example, when the board is full)."""
        terminal_state = False

        # fill in your code here!
        return terminal_state
