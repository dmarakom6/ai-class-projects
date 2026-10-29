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

# TODO:
# Click/Space to place a disc - DONE
# Choose who plays first
# Notify player when opponent must pass
# Game over screen

from __future__ import annotations

from dataclasses import replace
from math import inf
from typing import Final

from othello_tui.engine import OthelloEngine
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
    START_CURSOR,
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
    "Legal moves are highlighted · click a cell to place a disc"
)


def score_text(board: list[list[str]]) -> Text:
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
        """Posted when a square is clicked."""

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
        # The footer shows this hint only while the cursor sits on a legal move.
        Binding("space", "place_disc", "Place disc", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.engine = OthelloEngine()
        self.state = self.engine.new_game()
        self.cursor_row, self.cursor_col = START_CURSOR
        self.status_message = DEFAULT_STATUS
        self._play_hint = False  # is the space hint shown in the footer?
        self._load_opening()

    def compose(self) -> ComposeResult:
        legal = self._legal()
        with Vertical(id="top-chrome"):
            yield Static(
                "● OTHELLO vs MiniMax",
                id="title-bar",
                markup=False,
            )
            with Horizontal(id="hud"):
                yield StatPanel(
                    "ROUND",
                    f"{self.state.round_number:02d} / {TOTAL_ROUNDS:02d}",
                    id="stat-round",
                )
                yield StatPanel("TURN", piece_name(self.state.turn), id="stat-turn")
                yield StatPanel("SCORE", score_text(self.state.board), id="stat-score")
                yield StatPanel("MOVES", f"{len(legal):02d}", id="stat-moves")
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
        self.state = self.engine.new_game()
        self.cursor_row, self.cursor_col = START_CURSOR

    def _legal(self) -> set[tuple[int, int]]:
        """Squares the current player may play, as (row, column) pairs."""
        return {(m.row, m.col) for m in self.engine.legal_moves(self.state)}

    # -- painting -----------------------------------------------------------

    def _paint(self) -> None:
        """Redraw the board, the HUD and the status line from the game state."""
        cursor = (self.cursor_row, self.cursor_col)
        legal = self._legal()
        for cell in self.query(BoardCell):
            cell.paint(
                self.state.board[cell.row][cell.col],
                legal=(cell.row, cell.col) in legal,
                cursor=(cell.row, cell.col) == cursor,
            )

        self.query_one("#stat-round", StatPanel).set_value(
            f"{self.state.round_number:02d} / {TOTAL_ROUNDS:02d}"
        )
        turn_panel = self.query_one("#stat-turn", StatPanel)
        turn_panel.set_value(piece_name(self.state.turn))
        turn_panel.set_class(self.state.turn == BLACK, "turn-black")
        turn_panel.set_class(self.state.turn == WHITE, "turn-white")
        self.query_one("#stat-score", StatPanel).set_value(score_text(self.state.board))
        self.query_one("#stat-moves", StatPanel).set_value(f"{len(legal):02d}")

        self.status_message = self._describe(*cursor)
        self.query_one("#status-line", Static).update(self.status_message)
        self._sync_play_binding(legal)

    def _describe(self, row: int, col: int) -> str:
        """Text describing a square, shown in the status line."""
        label = cell_label(row, col)
        piece = self.state.board[row][col]
        if piece != EMPTY:
            return f"{label} holds a {piece_name(piece).lower()} disc"
        if (row, col) in self._legal():
            return f"{label} is a legal move in the current position"
        return f"{label} is not a legal move in the current position"

    # -- interaction --------------------------------------------------------

    @on(BoardCell.Selected)
    def _on_cell_selected(self, event: BoardCell.Selected) -> None:
        """A square was clicked: move the cursor there and place a disc on it."""
        self.cursor_row, self.cursor_col = event.row, event.col
        self._place_disc(*self.engine.minimax(self.engine.__getstate__()))
        self._place_disc(event.row, event.col)

    def action_move_cursor(self, direction: str) -> None:
        """Move the keyboard cursor one square in the given direction."""
        d_row, d_col = DIRECTIONS[direction]
        self.cursor_row = (self.cursor_row + d_row) % BOARD_SIZE
        self.cursor_col = (self.cursor_col + d_col) % BOARD_SIZE
        self._paint()

    # def action_place_disc(self) -> None:
        # """Place a disc on the square under the keyboard cursor."""
        # self._place_disc(self.cursor_row, self.cursor_col)
        # self._place_disc(*self.engine.minimax(a,b, self.engine.__getstate__()))

    def _place_disc(self, row: int, col: int) -> None:
        """Play (row, col) for the current player; report illegal attempts."""
        move = self.engine.find(self.state, row, col)  # calls flips()
        if move is None:
            self._paint()
            self._set_status(f"Illegal move: {cell_label(row, col)} is not playable")
            return
        self.state = self.engine.play(self.state, move)  # new state, discs flipped
        self._paint()
        self._set_status(
            f"Placed on {cell_label(row, col)} · flipped {len(move.flips)} disc(s)"
        )

    def _set_status(self, message: str) -> None:
        """Replace the text shown in the status line."""
        self.status_message = message
        self.query_one("#status-line", Static).update(message)

    def _sync_play_binding(self, legal: set[tuple[int, int]]) -> None:
        """Show the space hint in the footer only over a legal move."""
        playable = (self.cursor_row, self.cursor_col) in legal
        if playable == self._play_hint:
            return
        for key, bindings in self._bindings.key_to_bindings.items():
            self._bindings.key_to_bindings[key] = [
                replace(binding, show=playable) if binding.action == "place_disc" else binding
                for binding in bindings
            ]
        self._play_hint = playable
        self.refresh_bindings()

    def action_reset(self) -> None:
        """Start over: back to the opening position."""
        self._load_opening() # reset state and cursor pos
        self.status_message = DEFAULT_STATUS
        self._paint()
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
