import Board
def main():
    board = Board.Board(8,9)
    board.printBoard()
    board.placeDisk(3,2,2)
    board.printBoard()

main()