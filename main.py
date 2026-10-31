import time

from board import BOARD_SIZE, EMPTY, O, SYMBOLS, X, Board
from player import Player


def ask_move(board: Board, letter: int) -> tuple[int, int]:
    """Ask the human, who plays letter, for a move until a valid one is given.
    Rows and columns are numbered 0 to BOARD_SIZE - 1."""
    allowed = [str(number) for number in range(BOARD_SIZE)]  # "0", "1", ..., as the human types them.
    while True:
        answer = input("Your move (row col): ").split()
        if len(answer) == 2 and all(number in allowed for number in answer):
            row, col = int(answer[0]), int(answer[1])
            if board.is_valid_move(row, col, letter):
                return row, col
        print(f"Please give a valid move as two numbers from 0 to {BOARD_SIZE - 1}, e.g. 2 3")


def main() -> None:
    # fill in your code here! As the assignment asks, the program must:
    depth = input("Give maximum search depth (integer)")
    turn = input("Type 'X' if you want to play first else 'O' ")
    board = Board(None,O)
    
    #   - ask the user for the maximum search depth, and whether they want to play first;
    #   - print the board after every move;
    #   - when the player to move has no valid move, say so and let the other player play;
    #   - say who won when the game is over.
    pass  # a function needs at least one statement; remove this line once you add your code.


if __name__ == "__main__":
    main()
