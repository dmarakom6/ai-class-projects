import Node
class Board:
    def __init__(self,boardWidth,boardHeight):
        self.boardWidth = boardWidth
        self.boardHeight = boardHeight
        self.arrayBoard = [[0]*boardWidth]*boardHeight # boardWidth = number of columns, boardHeight = number of rows
        for i in range(0,boardHeight):
            for j in range(0,boardWidth):
                self.arrayBoard[i][j] = Node.Node(i,j,0)

    def printBoard(self):
        for list in self.arrayBoard:
            row = "" 
            for node in list:
                row += node.__str__() + " "
            print(row)
        print("\n")

   #TODO method for checking occupied lines

    def placeDisk(self,posX,posY,diskColor):
        if( 1 <= posX <= self.boardWidth and 1 <= posY <= self.boardHeight):
            self.arrayBoard[posX][posY].setDiskColor(diskColor)