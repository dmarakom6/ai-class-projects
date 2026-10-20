
class Node:
    def __init__(self,posX,posY,diskColor):
        self.posX = posX
        self.posY = posY
        self.diskColor = diskColor # disk color takes values from [0,2],
        self.leftNeighbour = None   # 0 is colorless ( no disk in the node )
        self.rightNeighbour = None   # 1 is black, 2 is white
        self.topNeighbour = None
        self.downNeighbour = None
        self.leftTopDiagonalNeighbour = None
        self.rightTopDiagonalNeighbour = None
        self.leftDownDiagonalNeighbour = None
        self.rightDownDiagonalNeighbour = None

    def __repr__(self):
        if( self.diskColor == 0):
            return "E"  # "E" will symbolize empty node ( no disk on it)
        elif (self.diskColor == 1):
            return "B" # "B" for Black
        else:
            return "W" # "W" for White

        #TODO initialising neighbours

    def setDiskColor(self,diskColor):
        if( diskColor == 0 or diskColor == 1 or diskColor == 2 ):
            self.diskColor = diskColor