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

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Piece-square table for evaluate(): corners are worth the most because they can never be
# flipped, the squares next to them (-50, -20) are traps that hand the corner to the opponent,
# edges are solid, the centre is nearly worthless. Only the ratios matter.
WEIGHTS: Grid = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 8, 1, 1, 8, -2, 10],
    [5, -2, 1, 1, 1, 1, -2, 5],
    [5, -2, 1, 1, 1, 1, -2, 5],
    [10, -2, 8, 1, 1, 8, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100],
]


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
        # who plays first. A new board says that O played last, so X plays first. A pass is not a move,
        # so a passing player cannot record it here: whoever drives the game (main() or another loop)
        # must move the turn on when a player passes, otherwise the same player is asked to move twice.
        self.last_player = last_player
        # the move that led to this board (no move yet for a new board).
        self.last_move = Move()

    def copy(self) -> Board:
        board = Board(self.game_board, self.last_player)
        board.last_move = self.last_move
        return board

    def __str__(self) -> str:
        label_width = len(str(BOARD_SIZE - 1))  # room for the widest row number
        # each row is "* " + BOARD_SIZE symbols with spaces between them + " *", so 2 * BOARD_SIZE + 3 characters.
        border = " " * (label_width + 1) + "*" * (2 * BOARD_SIZE + 3)
        columns = " " * (label_width + 3) + " ".join(str(col) for col in range(BOARD_SIZE))
        rows = (
            f"{row:>{label_width}} " + "* " + " ".join(SYMBOLS[cell] for cell in self.game_board[row]) + " *"
            for row in range(BOARD_SIZE)
        )
        return "\n".join([columns, border, *rows, border])

    def make_move(self, row: int, col: int, letter: int) -> None:
        """Place a piece of letter at (row, col), flip the opponent's pieces it outflanks, remember the move."""
        # a square off the board means a bug, e.g. playing Move(-1, -1) when there was no valid move: that
        # player must pass instead. Without this check, Python's negative indices would fill a wrong square.
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise ValueError(f"({row}, {col}) is not on the board; a player with no valid move must pass.")
        # a move that is not valid means a bug somewhere else (e.g. a search that answered for the wrong
        # player). Refuse it here: without this check an illegal move is played silently
        if not self.is_valid_move(row, col, letter):
            raise ValueError(f"({row}, {col}) is not a legal move for {SYMBOLS[letter]}.")
        self.game_board[row][col] = letter

        for dr, dc in DIRECTIONS:
            line = []
            r, c = row + dr, col + dc
            # collect the run of opponent pieces in this direction, starting at the new piece
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.game_board[r][c] == -letter:
                line.append((r, c))
                r += dr
                c += dc
            # the run only counts if our own piece closes it at the far end; then flip the whole run
            if line and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.game_board[r][c] == letter:
                for flip_row, flip_col in line:
                    self.game_board[flip_row][flip_col] = letter
        self.last_move = Move(row, col)
        self.last_player = letter

    def is_valid_move(self, row: int, col: int, letter: int) -> bool:
        """True if letter may play at (row, col): the square is empty and the move outflanks opponent pieces."""
        is_valid = False

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.game_board[row][col] == EMPTY:
            for dr, dc in DIRECTIONS:
                # the next square must hold an opponent piece: at least one to outflank
                r, c = row + dr, col + dc
                if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.game_board[r][c] == -letter):
                    continue
                r += dr
                c += dc
                # skip the rest of the opponent's run
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.game_board[r][c] == -letter:
                    r += dr
                    c += dc
                # a piece of ours at the end closes the sandwich
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.game_board[r][c] == letter:
                    is_valid = True
                    break
        return is_valid

    def get_children(self, letter: int) -> list[Board]:
        """One child board for every valid move of letter, most attractive squares first.""" # Which is why we use -WEIGHTS in the lamba function below.
        children = []

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.is_valid_move(row, col, letter):
                    # copy() first, so the search tree keeps parents intact while children change
                    child = self.copy()
                    child.make_move(row, col, letter)
                    children.append(child)
        # alpha-beta prunes far more when the best moves come first: the table says how much a
        # square is worth to whoever sits on it, so both players want the high-weight squares
        # first (corners and edges before the traps next to the corners).
        children.sort(key=lambda child: -WEIGHTS[child.last_move.row][child.last_move.col])
        return children

    def evaluate(self) -> int:
        """The heuristic value of the board: positive is good for X (MAX), negative is good for O (MIN)."""
        score = 0

        # a finished game is scored exactly: with cells +1/-1, the plain sum is X pieces - O pieces
        if self.is_terminal():
            for row in self.game_board:
                score += sum(row)
            return score
        # mid-game, weight each piece by the square it sits on
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                score += WEIGHTS[row][col] * self.game_board[row][col]
        return score

    def is_terminal(self) -> bool:
        """The game is over when neither player has a valid move (for example, when the board is full)."""
        terminal_state = True

        # one legal move for either side is enough to keep the game alive
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.game_board[row][col] == EMPTY:
                    if self.is_valid_move(row, col, X) or self.is_valid_move(row, col, O):
                        terminal_state = False
                        return terminal_state
        return terminal_state
