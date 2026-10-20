"""Othello (Reversi) terminal interface built with Textual.

This is the **interface only**: an 8x8 grid you can click, the possible moves
highlighted on the board, and the round / turn / score always visible at the
top of the terminal.

Launching the app -- and pressing ``r`` -- starts from the classic opening
position: four discs in the middle of the grid, two black and two white, each
colour on one diagonal of the central 2x2 block.

Run it with::
    python -m othello_tui.app        # or: othello-tui
"""

# TODO: Choose who plays first, Bridge with Engine

from __future__ import annotations

from typing import Final

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Static

from othello_tui.demo import (
    BLACK,
    BOARD_SIZE,
    START_BOARD,
    START_CURSOR,
    START_MOVES,
    START_ROUND,
    START_TURN,
    TOTAL_ROUNDS,
    EMPTY,
    WHITE,
    cell_label,
    count_discs,
    piece_name,
)

#: The interface is monochrome: black and white discs, grey board.
DISC_GLYPH: Final[str] = "●"  # black circle, recoloured per disc colour
HINT_GLYPH: Final[str] = "○"  # outline of a disc, for a possible move
BLANK_GLYPH: Final[str] = " "

DIRECTIONS: Final[dict[str, tuple[int, int]]] = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}

DEFAULT_STATUS: Final[str] = (
    f"{len(START_MOVES)} possible moves are highlighted · "
    "click a cell to inspect it"
)


def score_text(board: list[str]) -> Text:
    """Disc counts drawn with black and white only."""
    return Text.assemble(
        (DISC_GLYPH, "black on white"),
        f" {count_discs(board, BLACK):02d}",
        "   ",
        (DISC_GLYPH, "white on black"),
        f" {count_discs(board, WHITE):02d}",
    )


class StatPanel(Vertical):
    """A small panel with a label and a value."""

    def __init__(self, label: str, value: str | Text, *, id: str | None = None) -> None:
        super().__init__(id=id, classes="stat")
        self._label = label
        self._value = value

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="stat-label", markup=False)
        yield Static(self._value, classes="stat-value", markup=False)

    def set_value(self, value: str | Text) -> None:
        """Replace the value shown under the label."""
        self.query_one(".stat-value", Static).update(value)


class BoardCell(Static):
    """A single clickable square of the board."""

    can_focus = True

    class Selected(Message):
        """Posted when a square is clicked, or activated from the keyboard."""

        def __init__(self, row: int, col: int) -> None:
            super().__init__()
            self.row = row
            self.col = col

    def __init__(self, row: int, col: int, *, classes: str = "") -> None:
        super().__init__(
            BLANK_GLYPH,
            id=f"cell-{row}-{col}",
            classes=f"cell {classes}".strip(),
            markup=False,
        )
        self.row = row
        self.col = col

    def paint(self, piece: str, *, legal: bool, cursor: bool) -> None:
        """Show a square's content (disc, possible move or blank)."""
        self.set_class(piece == BLACK, "disc-black")
        self.set_class(piece == WHITE, "disc-white")
        self.set_class(legal, "legal")
        self.set_class(cursor, "cursor")
        if piece != EMPTY:
            glyph = DISC_GLYPH
        elif legal:
            glyph = HINT_GLYPH
        else:
            glyph = BLANK_GLYPH
        self.update(glyph)

    def on_click(self, event: Click) -> None:
        self.focus()
        self.post_message(self.Selected(self.row, self.col))


class Board(Vertical):
    """The 8x8 grid of :class:`BoardCell` squares."""

    def compose(self) -> ComposeResult:
        for row in range(BOARD_SIZE):
            with Horizontal(classes="board-row"):
                for col in range(BOARD_SIZE):
                    extras = " ".join(
                        name
                        for name, needed in (
                            ("last-col", col == BOARD_SIZE - 1),
                            ("last-row", row == BOARD_SIZE - 1),
                        )
                        if needed
                    )
                    yield BoardCell(row, col, classes=extras)


class OthelloScreen(Screen):
    """The single screen: title, HUD, board and status line."""

    BINDINGS = [
        # "quit" lives on the App, so the action is namespaced.
        Binding("q", "app.quit", "Quit"),
        Binding("r", "reset", "Reset"),
        Binding("up", "move_cursor('up')", "Move up", show=False),
        Binding("down", "move_cursor('down')", "Move down", show=False),
        Binding("left", "move_cursor('left')", "Move left", show=False),
        Binding("right", "move_cursor('right')", "Move right", show=False),
        Binding("enter,space", "select_cursor", "Inspect cell"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.board: list[list[str]] = []
        self.legal_moves: set[tuple[int, int]] = set()
        self.turn = START_TURN
        self.round_number = START_ROUND
        self.cursor_row, self.cursor_col = START_CURSOR
        self.status_message = DEFAULT_STATUS
        self._load_opening()

    def compose(self) -> ComposeResult:
        with Vertical(id="top-chrome"):
            yield Static(
                "● OTHELLO vs MiniMax",
                id="title-bar",
                markup=False,
            )
            with Horizontal(id="hud"):
                yield StatPanel(
                    "ROUND",
                    f"{self.round_number:02d} / {TOTAL_ROUNDS:02d}",
                    id="stat-round",
                )
                yield StatPanel("TURN", piece_name(self.turn), id="stat-turn")
                yield StatPanel("SCORE", score_text(self.board), id="stat-score")
                yield StatPanel("MOVES", f"{len(self.legal_moves):02d}", id="stat-moves")
        with Container(id="stage"):
            yield Board(id="board")
        with Vertical(id="bottom-chrome"):
            yield Static(self.status_message, id="status-line", markup=False)
            yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Paint the opening position once the widgets exist."""
        self._paint()

    # -- game state ----------------------------------------------------------

    def _load_opening(self) -> None:
        """Start from the opening position."""
        self.board = [list(row) for row in START_BOARD]
        self.legal_moves = set(START_MOVES)
        self.turn = START_TURN
        self.round_number = START_ROUND
        self.cursor_row, self.cursor_col = START_CURSOR

    # -- painting -----------------------------------------------------------

    def _paint(self) -> None:
        """Redraw the board, the HUD and the status line from the game state."""
        cursor = (self.cursor_row, self.cursor_col)
        for cell in self.query(BoardCell):
            cell.paint(
                self.board[cell.row][cell.col],
                legal=(cell.row, cell.col) in self.legal_moves,
                cursor=(cell.row, cell.col) == cursor,
            )

        self.query_one("#stat-round", StatPanel).set_value(
            f"{self.round_number:02d} / {TOTAL_ROUNDS:02d}"
        )
        turn_panel = self.query_one("#stat-turn", StatPanel)
        turn_panel.set_value(piece_name(self.turn))
        turn_panel.set_class(self.turn == BLACK, "turn-black")
        turn_panel.set_class(self.turn == WHITE, "turn-white")
        self.query_one("#stat-score", StatPanel).set_value(score_text(self.board))
        self.query_one("#stat-moves", StatPanel).set_value(f"{len(self.legal_moves):02d}")

        self.status_message = self._describe(*cursor)
        self.query_one("#status-line", Static).update(self.status_message)

    def _describe(self, row: int, col: int) -> str:
        """Text describing a square, shown in the status line."""
        label = cell_label(row, col)
        piece = self.board[row][col]
        if piece != EMPTY:
            return f"{label} holds a {piece_name(piece).lower()} disc"
        if (row, col) in self.legal_moves:
            return (
                f"{label} is a legal move in the current position · "
            )
        return f"{label} is not a legal move in the current position"

    # -- interaction --------------------------------------------------------

    @on(BoardCell.Selected)
    def _on_cell_selected(self, event: BoardCell.Selected) -> None:
        """A square was clicked (or activated): move the cursor and report it."""
        self.cursor_row, self.cursor_col = event.row, event.col
        self._paint()

    def action_move_cursor(self, direction: str) -> None:
        """Move the keyboard cursor one square in the given direction."""
        d_row, d_col = DIRECTIONS[direction]
        self.cursor_row = (self.cursor_row + d_row) % BOARD_SIZE
        self.cursor_col = (self.cursor_col + d_col) % BOARD_SIZE
        self._paint()

    def action_select_cursor(self) -> None:
        """Report the square under the keyboard cursor."""
        self._paint()

    def action_reset(self) -> None:
        """Start over: back to the opening position."""
        self._load_opening()
        self._paint()
        self.status_message = DEFAULT_STATUS
        self.query_one("#status-line", Static).update(DEFAULT_STATUS)


class OthelloApp(App[None]):
    """A terminal Othello board -- interface only for now."""

    TITLE = "Othello"
    SUB_TITLE = "Reversi"
    CSS_PATH = "app.tcss"

    def on_mount(self) -> None:
        self.push_screen(OthelloScreen())


def run() -> None:
    """Entry point of the ``othello-tui`` console script."""
    OthelloApp().run()


if __name__ == "__main__":
    run()
