Othello vs Minimax
==================

Textual interface for an Othello (Reversi) game simulation.

To run the game:

Install the uv python package manager:

```
pip install uv
```

Then, from the project root:

```
uv sync
uv run othello-tui
```

`uv sync` creates `.venv` on first use and updates it in place on later runs, so
nothing asks for confirmation. `uv run othello-tui` syncs on demand before
starting, so `uv sync` is optional if you only want to play.

If you prefer to create the environment by hand with `uv venv .venv`, uv will
ask to replace the existing one on every later run. Pass `--clear` to skip that prompt.
