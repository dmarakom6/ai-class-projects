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
    #   - ask the user for the maximum search depth, and whether they want to play first;
    #   - print the board after every move;
    #   - when the player to move has no valid move, say so and let the other player play;
    #   - say who won when the game is over.
    # keep asking until the depth is a positive number
    while True:
        answer = input("Maximum search depth: ").split()
        if len(answer) == 1 and answer[0].isdigit() and int(answer[0]) > 0:
            max_depth = int(answer[0])
            break
        print("Please give a positive number, e.g. 4")

    while True:
        answer = input("Do you want to play first? (y/n): ").strip().lower()
        if answer in ("y", "n"):
            break
        print("Please answer y or n")

    human_letter = X if answer == "y" else O
    ai_letter = -human_letter  # pieces are +1/-1, so negation swaps the two players
    ai = Player(max_depth, ai_letter)
    board = Board()
    current = X  # X always plays first, whoever plays it

    print(f"You play {SYMBOLS[human_letter]}, the computer plays {SYMBOLS[ai_letter]}.")
    while True:
        print(board)
        if board.is_terminal():
            break
        if not any(board.is_valid_move(row, col, current) for row in range(BOARD_SIZE) for col in range(BOARD_SIZE)):
            # a pass is not a move: no board change, the turn just goes to the other player
            print(f"{SYMBOLS[current]} has no valid move and must pass.")
            current = -current
            continue
        if current == human_letter:
            row, col = ask_move(board, current)
        else:
            started = time.perf_counter()
            move = ai.alpha_beta(board)
            elapsed = time.perf_counter() - started
            row, col = move.row, move.col
            print(f"Computer plays {row} {col} (searched {ai.visited_nodes} boards in {elapsed:.2f}s)")
        board.make_move(row, col, current)
        current = -current

    # count the pieces to decide the winner
    x_count = sum(row.count(X) for row in board.game_board)
    o_count = sum(row.count(O) for row in board.game_board)
    if x_count > o_count:
        winner = X
    elif o_count > x_count:
        winner = O
    else:
        winner = EMPTY  # EMPTY means a draw here
    print(f"X has {x_count} pieces, O has {o_count} pieces.")
    if winner == EMPTY:
        print("The game is a draw.")
    elif winner == human_letter:
        print("You win!")
    else:
        print("The computer wins!")


if __name__ == "__main__":
    main()
