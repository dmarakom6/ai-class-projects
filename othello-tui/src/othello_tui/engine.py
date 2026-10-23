# TODO Our names / Α.Μ.'s here.
# Othello (Reversi) engine.
# Read ARCHITECTURE.md
#
# TODO: Engine (implement flips()),
# A-B Minimax Solver (in a new function here called `minimax`),
# Bridge with TUI,
# Test Drive,
# Docs (PDF with test cases)

"""The rules of Othello (Reversi), and nothing else."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from othello_tui.demo import (
    BLACK,
    BOARD_SIZE,
    EMPTY,
    START_BOARD,
    START_ROUND,
    START_TURN,
    WHITE,
    count_discs,
)

#: The eight directions a capture line can run in, as (row, column) steps.
#: These replace the eight named neighbours of the sketch's ``Node``.
DIRECTIONS: Final[list[tuple[int, int]]] = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
]


@dataclass
class GameState:
    """A position: the board, whose turn it is, and how far the game is."""

    board: list[list[str]]  # 8x8 of "B" / "W" / "."
    turn: str
    round_number: int = 1


@dataclass(frozen=True)
class Move:
    """One legal play: where the disc goes and what it captures."""

    row: int
    col: int
    flips: tuple[tuple[int, int], ...]  # squares this move would capture


def opponent(piece: str) -> str:
    """The other colour."""
    return {BLACK: WHITE, WHITE: BLACK}[piece] # This is called a lookup table


def flips(board: list[list[str]], row: int, col: int, piece: str) -> list[tuple[int, int]]:
    """Discs captured by playing `piece` at (row, col); empty means illegal."""

    tuplesList = []
    r = row - 1
    while ( r >= 0): # check top neighbor path.
        if(board[r][col] == EMPTY): # if you see empty node stop the search, we can't flip disks
            break
        if(board[r][col] == piece): # if you see node which has a disc of same color, you managed to flip disks
            for i in range(row-1,r+1):
                tuplesList.append(tuple(i,col))
            break
        r -= 1 # decrease r by 1, go on your top neighbour

    r = row + 1
    while ( r <= BOARD_SIZE-1): # check bottom neighbour path
        if(board[r][col] == EMPTY):
            break
        if(board[r][col] == piece):
            for i in range(row+ 1,r+1):
                tuplesList.append(tuple(i,col))
            break
        r += 1 # increase r by 1, go on your bottom neighbour

    c = col - 1
    while ( c >= 0): # check left neighbour path
        if(board[row][c] == EMPTY):
            break
        if(board[row][c] == piece):
            for i in range(col-1,c+1):
                tuplesList.append(tuple(row,i))
            break
        c -= 1 # decrease r by 1, go on your left neighbour

    c = col + 1
    while ( c <= BOARD_SIZE-1): # check right neighbour path
        if(board[row][c] == EMPTY):
            break
        if(board[row][c] == piece):
            for i in range(col+1,c+1):
                tuplesList.append(tuple(row,i))
            break
        c += 1  # increase r by 1, go on your right neighbour

    r = row - 1
    c = col - 1
    while( c >= 0 and r >= 0): # check left top neighbour path
        if(board[r][c] == EMPTY):
            break
        if(board[r][c] == piece):
            rowN = row - 1
            colN = col - 1
            while( rowN >= r and colN >= c):
                tuplesList.append(tuple(rowN,colN))
                rowN -= 1
                colN -=1
            break
        c -= 1  # go to left top neighbour
        r -= 1

    r = row - 1
    c = col + 1
    while( c <= BOARD_SIZE - 1 and r >= 0): # check right top neighbour path
        if(board[r][c] == EMPTY):
            break
        if(board[r][c] == piece):
            rowN = row - 1
            colN = col + 1
            while( rowN >= r and colN <= c): 
                tuplesList.append(tuple(rowN,colN))
                rowN -= 1
                colN +=1
        c += 1  # go to right top neighbour
        r -= 1

    r = row + 1
    c = col - 1
    while( c >= 0 and r <= BOARD_SIZE-1): # check left bottom neighbour path
        if(board[r][c] == EMPTY):
            break
        if(board[r][c] == piece):
            directionsList.append(tuple(-1,1))
            break
        c -= 1  # go to left bottom neighbour
        r += 1

    r = row + 1
    c = col + 1
    while( c <= BOARD_SIZE-1 and r <= BOARD_SIZE-1): # check right bottom neighbour path
        if(board[r][c] == EMPTY):
            break
        if(board[r][c] == piece):
            directionsList.append(tuple(1,1))
            break
        c += 1  # go to right bottom neighbour
        r += 1   

    return directionsList


    



class OthelloEngine:
    """Everything the interface needs, and nothing else."""

    def new_game(self) -> GameState:
        """Opening position, black to move, round 1."""
        return GameState(
            board=[list(row) for row in START_BOARD],
            turn=START_TURN,
            round_number=START_ROUND,
        )

    def legal_moves(self, state: GameState) -> list[Move]:
        """Every legal move for state.turn, with the discs it flips."""
        return self._moves(state.board, state.turn)

    def find(self, state: GameState, row: int, col: int) -> Move | None:
        """The legal move for these coordinates, or None if the square is illegal.""" # we pass the result to play()
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return None
        captured = flips(state.board, row, col, state.turn)
        return Move(row, col, tuple(captured)) if captured else None

    def play(self, state: GameState, move: Move) -> GameState:
        """Return a *new* state with the move applied (discs flipped, turn passed)."""
        piece = state.turn
        board = [list(row) for row in state.board]
        board[move.row][move.col] = piece
        for row, col in move.flips:
            board[row][col] = piece  # flip the captured discs - needs flips()!

        next_turn = opponent(piece)
        if not self._moves(board, next_turn) and self._moves(board, piece):
            next_turn = piece  # the opponent must pass: the turn comes back
        return GameState(
            board=board,
            turn=next_turn,
            round_number=state.round_number + 1,
        )


    # -- TUI stuff --

    def score(self, state: GameState) -> tuple[int, int]:
        """(black discs, white discs)."""
        return (count_discs(state.board, BLACK), count_discs(state.board, WHITE))

    def is_over(self, state: GameState) -> bool:
        """No legal move for either player.""" # Check every new round
        return not self._moves(state.board, BLACK) and not self._moves(
            state.board, WHITE
        )

    def _moves(self, board: list[list[str]], piece: str) -> list[Move]:
        """Every legal move for one colour on a bare board, in reading order."""
        return [
            Move(row, col, tuple(captured))
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
            if (captured := flips(board, row, col, piece))
        ]
