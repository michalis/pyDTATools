__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from transNetwork.vertex import Vertex

class Centroid(Vertex):

    def __init__(self, id_, x, y):

        super(Centroid, self).__init__(id_, x, y)

    def __repr__(self):
        """Return a tab delimited string representation of the node"""
        return "%s\t%d\t%d\t%d" % (self._iid, 100, self.x, self.y)

    def isCentroid(self):
        return True

    def isNode(self):
        return False
