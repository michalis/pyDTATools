__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from collections import defaultdict
from itertools import izip
from operator import itemgetter 

from pbCore.utils.itertools2 import pairwise
from pbCore.geometry.lineString import LineString, angleBetweenLineStrings
from errors import MovementError

class Movement(LineString):
    """Represents a movement between 3 succesive nodes"""

    TURN_LEFT = 0
    TURN_THRU = 1
    TURN_RIGHT = 2
    TURN_OTHER1 = 3
    TURN_OTHER2 = 4
    TURN_UTURN = 5
    LANE_CAPACITY = 1900
    
    LINK_UTURN_YES = "1"
    LINK_UTURN_NO = "0"
    
    directions = [TURN_LEFT, TURN_THRU, TURN_RIGHT, \
                      TURN_OTHER1, TURN_OTHER2]

    def __init__(self, upLink, downLink, turnType):
        """Constructor. Enter 3 successive NODES not nodeId strings"""
        super(Movement, self).__init__([upLink.nodeA, upLink.nodeB, downLink.nodeB])
        self.upLink = upLink
        self.downLink = downLink
        self.nodeA = upLink.nodeA
        self.nodeB = upLink.nodeB
        self.nodeC = downLink.nodeB
        self.nodeAid = self.nodeA.id
        self.nodeBid = self.nodeB.id
        self.nodeCid = self.nodeC.id
        #TODO self.direction is wrong
        self.direction = turnType
        self.turnType = turnType
        if self.upLink.nodeAid == self.downLink.nodeBid:
            self.turnType = Movement.TURN_UTURN

        self.iid = (self.nodeAid, self.nodeBid, self.nodeCid)

        self._numLanes = 0 

    def setNumLanes(self, numLanes):
        """Set the number of lanes the movement serves"""
        self._numLanes = numLanes
        self._calcCapacity()

    def getNumLanes(self):
        """Return the number of lanes the movement operates on"""
        return self._numLanes

    def _calcCapacity(self):
        """Calculate the capacity of the movement"""
        self._capacity = self._numLanes * Movement.LANE_CAPACITY

    def getCapacity(self):
        #TODO: is capacity what I want? or saturation flow?
        return self._capacity
    
    def __str__(self):
        """Return a string representation of the movement for printing purposes"""
        return self.__repr__()

    def __repr__(self):
        """Return a string represenation of the movement"""
        return "%7s" * 4 % (self.nodeAid, self.nodeBid, self.nodeCid, self.direction)
        
    def getAngle(self):

        return angleBetweenLineStrings(self.upLink, self.downLink)

    def isLeftTurn(self):
        """Return True if the movement is classified as left False otherwise"""
        return True if self.turnType == Movement.TURN_LEFT else False

    def isThruTurn(self):
        """Return True if the movement is classified as Thru False otherwise"""
        return True if self.turnType == Movement.TURN_THRU else False

    def isRightTurn(self):
        return True if self.turnType == Movement.TURN_RIGHT else False

    def isOther1Turn(self):
        return True if self.turnType == Movement.TURN_OTHER1 else False        

    def isOther2Turn(self):
        return True if self.turnType == Movement.TURN_OTHER2 else False            

    def isUTurn(self):
        """Return True if the movement makes a U Turn"""
        return True if self.turnType == Movement.TURN_UTURN else False

    def getTypeAsString(self):
        """Return the type of the movement decoded"""
        if self.turnType == Movement.TURN_LEFT:
            return "Turn left"
        elif self.turnType == Movement.TURN_THRU:
            return "Thru"
        elif self.turnType == Movement.TURN_RIGHT:
            return "Turn right"
        elif self.turnType == Movement.TURN_OTHER1:
            return "Turn other1"
        elif self.turnType == Movement.TURN_OTHER2:
            return "Turn other2"
        else:
            return "U turn"        
