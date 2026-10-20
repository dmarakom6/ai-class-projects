# othello-tui — implementation guide

How this CLI is built, and how we put a real Othello algorithm behind it.



### The shape of the project

```
othello-tui/
├── pyproject.toml                 # packaging and the console script
├── uv.lock                        # pinned dependencies
├── ARCHITECTURE.md                # this document
├── scratch/                       # the first Node/Board/main sketch, kept for reference
└── src/othello_tui/
    ├── demo.py                    # game state fixtures (the "position")
    ├── engine.py                  # the rules: legal moves, captures, passing (no Textual)
    ├── app.py                     # widgets, screen, interaction
    └── app.tcss                   # Textual CSS (layout + monochrome theme)
```

Layers, with strictly one job each:

| Layer | File | Responsibility |
| --- | --- | --- |
| Data | `demo.py` | The position: board, whose turn, legal squares, HUD numbers |
| Rules | `engine.py` | Legal moves, captures, passing, game over (no Textual) |
| Behaviour | `app.py` | Widgets, events, actions; *reads the position and paints it* |
| Presentation | `app.tcss` | Where things go and how they look (black/white/grey only) |



### Runtime flow

```
run()
 └─ OthelloApp().run()                  # App owns the CSS, pushes the screen
     └─ OthelloScreen                   # Screen owns state + interaction
         ├─ compose()                   # builds the widget tree
         ├─ on_mount() -> _paint()      # first paint from the opening position
         ├─ BoardCell.Selected (message) # user clicked a square
         └─ BINDINGS / action_*         # keys: arrows, enter, r, q
```

> `run()` is also the console script entry point declared in `pyproject.toml`

### `demo.py`

The whole "game" is one module of constants plus three tiny helpers:

```python
EMPTY: Final = "."
BLACK: Final = "B"
WHITE: Final = "W"

#: Opening position: white on d4/e5, black on e4/d5 (a1 is the top left).
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

#: Squares highlighted as playable, as (row, column) pairs.
START_MOVES: Final[frozenset[tuple[int, int]]] = frozenset(
    {(2, 3), (3, 2), (4, 5), (5, 4)}   # d3, c4, f5, e6
)

START_TURN: Final = BLACK   # black always starts
START_ROUND: Final = 1
TOTAL_ROUNDS: Final = 60               # 60 empty squares at the start
START_CURSOR: Final[tuple[int, int]] = (2, 3)   # d3 by convention
```

**Coordinate convention** (used everywhere, tests included):

| Concept | Type | Example |
| --- | --- | --- |
| Square | `(row, col)`, both `0..7`, top-left origin | `(2, 3)` |
| Board | 8 strings of 8 chars, one per row | `START_BOARD[3] == "...WB..."` |
| Label | `cell_label(row, col)` | `cell_label(2, 3) == "d3"` |

So `a1` is `(0, 0)` and `h8` is `(7, 7)` — Othello notation, not chess
notation. Keeping the mapping in one helper (`cell_label`) means the status
line, the tests and a future log all agree.

The board uses single characters (`"B"`, `"W"`, `"."`) because it makes the
fixture readable in source and trivially comparable in tests.

### `BoardCell`

Each of the 64 squares is a `Static` subclass that knows its coordinates, can
be clicked, and can repaint itself from a few booleans:

```python
class BoardCell(Static):
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
        self.set_class(piece == BLACK, "disc-black")
        self.set_class(piece == WHITE, "disc-white")
        self.set_class(legal, "legal")
        self.set_class(cursor, "cursor")
        if piece != EMPTY:
            glyph = DISC_GLYPH          # "●"
        elif legal:
            glyph = HINT_GLYPH          # "○"
        else:
            glyph = BLANK_GLYPH
        self.update(glyph)

    def on_click(self, event: Click) -> None:
        self.focus()
        self.post_message(self.Selected(self.row, self.col))
```

- **`Selected` is a custom message.** Widgets talk to their ancestors by
  posting messages; the screen handles them with the `@on(BoardCell.Selected)` decorator.

- **State is expressed as CSS classes**, using TCSS. `paint()` decides
  *what* the square is (`disc-black`, `disc-white`, `legal`, `cursor`);
  `app.tcss` decides the style.

- **`id=f"cell-{row}-{col}"`** makes every square addressable
  (`#cell-2-3`) in CSS, in `query_one()`.


### the 8×8 grid

A `Vertical` of eight `Horizontal` rows, one cell per row:

```python
class Board(Vertical):
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
```

Flexbox rows/columns (rather than a CSS grid) keep the geometry predictable.

### `OthelloScreen`

The screen owns the *current* position and is the only thing that mutates it.

```python
    def __init__(self) -> None:
        super().__init__()
        self.board: list[list[str]] = []          # 8x8 of "B" / "W" / "."
        self.legal_moves: set[tuple[int, int]] = set()
        self.turn = START_TURN
        self.round_number = START_ROUND
        self.cursor_row, self.cursor_col = START_CURSOR
        self.status_message = DEFAULT_STATUS
        self._load_opening()
```

Loading the opening position is one small method:
```python
    def _load_opening(self) -> None:
        """Start from the opening position."""
        self.board = [list(row) for row in START_BOARD]
        self.legal_moves = set(START_MOVES)
        self.turn = START_TURN
        self.round_number = START_ROUND
        self.cursor_row, self.cursor_col = START_CURSOR
```

Painting is a pure projection of that state onto widgets:

```python
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
```

The status line is written by `_describe()`, which basically turns a square into words:

```python
    def _describe(self, row: int, col: int) -> str:
        label = cell_label(row, col)
        piece = self.board[row][col]
        if piece != EMPTY:
            return f"{label} holds a {piece_name(piece).lower()} disc"
        if (row, col) in self.legal_moves:
            return (
                f"{label} is a legal move in the current position · "
                "no rules implemented yet, nothing was played"
            )
        return f"{label} is not a legal move in the current position"
```

### Interaction w/ messages and actions

```python
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
```

### `StatPanel` and the score

The HUD is four panels; each is a labelled box with a `set_value()` so the game
can refresh it later without rebuilding the layout:

```python
class StatPanel(Vertical):
    def __init__(self, label: str, value: str | Text, *, id: str | None = None) -> None:
        super().__init__(id=id, classes="stat")
        self._label = label
        self._value = value

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="stat-label", markup=False)
        yield Static(self._value, classes="stat-value", markup=False)

    def set_value(self, value: str | Text) -> None:
        self.query_one(".stat-value", Static).update(value)
```


---

## 2. Building the algorithm behind it

The screen keeps five pieces of state and one method that syncs the widgets to
them. That is the entire API an engine has to satisfy:

| Member | Type | Read by | Written by |
| --- | --- | --- | --- |
| `board` | `list[list[str]]`, 8×8 of `"B"` / `"W"` / `"."` | `_paint`, `_describe`, `score_text` | engine |
| `legal_moves` | `set[tuple[int, int]]` (row, col) | `_paint`, `_describe` | engine |
| `turn` | `"B"` or `"W"` | `_paint` (turn panel) | engine |
| `round_number` | `int` | `_paint` (HUD) | engine |
| `cursor_row`, `cursor_col` | `int` | `_paint`, actions | UI |
| `_paint()` | method | — | call it after **every** state change |

Rules of engagement:

1. Mutate the state, then call `_paint()`. Never touch widgets directly from
   outside the screen.
2. `legal_moves` is whatever you want to highlight — real legal moves, hints,
   or the output of a search. The UI just draws it.
3. `EMPTY` / `BLACK` / `WHITE` come from `demo.py`; reuse those constants so
   the UI and the engine speak the same language.
4. Coordinates are always `(row, col)` with `(0, 0)` at the top left.

### A suggested engine API

Keep the algorithm in its own module with **no Textual imports**.

```python
# src/othello_tui/engine.py
from dataclasses import dataclass

from othello_tui.demo import BLACK, BOARD_SIZE, EMPTY, WHITE

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


@dataclass
class GameState:
    board: list[list[str]]                  # 8x8 of "B" / "W" / "."
    turn: str
    round_number: int = 1


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    flips: tuple[tuple[int, int], ...]      # squares this move would capture


def opponent(piece: str) -> str:
    return {BLACK: WHITE, WHITE: BLACK}[piece]


class OthelloEngine:
    """Everything the interface needs, and nothing else."""

    def new_game(self) -> GameState:
        """Opening position, black to move, round 1."""

    def legal_moves(self, state: GameState) -> list[Move]:
        """Every legal move for state.turn, with the discs it flips."""

    def find(self, state: GameState, row: int, col: int) -> Move | None:
        """The legal move for these coordinates, or None if the square is illegal."""

    def play(self, state: GameState, move: Move) -> GameState:
        """Return a *new* state with the move applied (discs flipped, turn passed)."""

    def score(self, state: GameState) -> tuple[int, int]:
        """(black discs, white discs)."""

    def is_over(self, state: GameState) -> bool:
        """No legal move for either player."""
```

`play()` copies the board before flipping, so callers always get a fresh
`GameState` rather than a mutated one. That makes undo, animation and AI search
dramatically easier, and it maps cleanly onto `_paint()`.

Three small changes turn the preview into a game. First, hold the engine and
its state (replace the fixture loading):

```python
    def __init__(self) -> None:
        super().__init__()
        self.engine = OthelloEngine()
        self.state = self.engine.new_game()
        self.cursor_row, self.cursor_col = START_CURSOR
        self.status_message = DEFAULT_STATUS
```

Then have `_paint()` read from the state through the engine — one-line changes,
`self.board` becomes `self.state.board`, `self.legal_moves` becomes
`{(m.row, m.col) for m in self.engine.legal_moves(self.state)}`, `self.turn`
becomes `self.state.turn`, `self.round_number` becomes `self.state.round_number`.
Finally, make the click play a move:

```python
    @on(BoardCell.Selected)
    def _on_cell_selected(self, event: BoardCell.Selected) -> None:
        self.cursor_row, self.cursor_col = event.row, event.col
        move = self.engine.find(self.state, event.row, event.col)   # None if illegal
        if move is not None:
            self.state = self.engine.play(self.state, move)
            self.status_message = f"played {cell_label(event.row, event.col)}"
        else:
            self.status_message = self._describe(event.row, event.col)
        self._paint()
```

and the same for the keyboard path (`action_select_cursor`) and reset:

```python
    def action_reset(self) -> None:
        self.state = self.engine.new_game()
        self.cursor_row, self.cursor_col = START_CURSOR
        self._paint()
```

An optional nicety: expose the sync point publicly so external code (a REPL,
an AI worker, a test) has a supported way to change the position:

```python
    def set_state(self, state) -> None:
        """Replace the game state and repaint."""
        self.state = state
        self._paint()
```
## Rules

```python
def flips(board: list[list[str]], row: int, col: int, piece: str) -> list[tuple[int, int]]:
    """Discs captured by playing `piece` at (row, col); empty means illegal."""
    if board[row][col] != EMPTY:
        return []
    other = opponent(piece)
    captured: list[tuple[int, int]] = []
    for d_row, d_col in DIRECTIONS:
        line: list[tuple[int, int]] = []
        r, c = row + d_row, col + d_col
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == other:
            line.append((r, c))
            r, c = r + d_row, c + d_col
        if line and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
            captured.extend(line)          # sandwiched: closed by our own disc
    return captured
```

From that:

- **legal moves** — the empty squares where `flips(...)` is non-empty;
- **`play()`** — copy the board, set `board[row][col] = piece`, flip the
  captured discs, then pass the turn and bump the round;
- **pass** — if the *next* player has no legal move but the current one does,
  the turn comes back (and the round counter only advances on a real move);
- **game over** — neither player has a legal move (or all 64 squares are
  filled); the winner is `score()` compared.

Keep `play()` pure and the UI will never need to know any of this.

## Final bits

- **Turn / round / score** already read from state, so they update for free.
- **Game over**: `self.notify("Black wins 35–29")` for a toast, or push a modal
  `Screen` (a `Static` with a `Button`) via `self.push_screen(GameOverScreen(...))`
  and disable further clicks with `self.legal_moves = set()`.
- **AI opponent**: run the search off the UI thread and apply the result back - use Minimax algorithm here.

  ```python
  from textual import work

  @work(thread=True)
  def _think(self) -> None:
      move = self.engine.best_move(self.state, depth=4)   # blocking is fine here
      self.app.call_from_thread(self._play_move, move)

  def _play_move(self, move: Move) -> None:
      self.state = self.engine.play(self.state, move)
      self._paint()
  ```

---

The Textual docs worth reading next:
[tutorial](https://textual.textualize.io/tutorial/),
[guide to widgets](https://textual.textualize.io/guide/widgets/),
[events and messages](https://textual.textualize.io/guide/events/)
