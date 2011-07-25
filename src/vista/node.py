__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from roadNetwork.roadNode import RoadNode

class Node(RoadNode):

    def __init__(self, id_, x, y):

        super(Node, self).__init__(id_, x, y)
        self._timePlan = False

    def __repr__(self):
        """Return a tab delimited string representation of the node"""
        return "%s\t%d\t%d\t%d" % (self._iid, 1, self.x, self.y)

    def addTimePlan(self, timePlan):
        """Add a timeplan with the given offset and return a reference to it"""
        self._timePlan = timePlan

    def deleteTimePlan(self):
        """Delete the timePlan associated with the node"""
        self._timePlan = None

    def hasTimePlan(self):
        """Return True if the node has a time plan else false"""
        return True if self._timePlan else False

    def getTimePlan(self):
        """Return the timeplan attached to the node"""
        if self.timePlan:
            return self.timePlan
        else:
            raise TimePlanError("Node %d does not have a timeplan" % self.id)

    def isCentroid(self):
        return False

    def isNode(self):
        return True

