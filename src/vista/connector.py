__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from transNetwork.edge import Edge

class Connector(Edge):


    def __init__(self, id_, startVertex, endVertex,
                 speedInMilesPerMinute, saturationFlowPCPHGPL,
                 numMidBlockLanes):
                  
        super(Edge, self).__init__(startVertex, endVertex, numLanes)

    def addBay(self, bay):

        assert isinstance(bay, Bay)
        self._bays[bay.getSide(), bay.getType()] = bay

    def getBay(self, side, type_):

        return self._bays[bay.getSide(), bay.getType()]

    def iterBays(self):

        return self._bays.itervalues()

    def getNumBays(self):

        return len(self._bays)
        
    def isConnector(self):

        return True

    def isLink(self):

        return False

    def getId(self):

        return self._id

    def isConnector(self):

        return False

    def isLink(self):

        return True

    def __repr__(self):
        """Returns a few basic link attribues. The returned string
        looks like:
        1	100	1	[(2229186.658,1371165.3888),(2229622,1371277)]
        """        
        coords = ",".join(["(%.4f,%.4f)" % (p.x, p.y) for p in self.iterPoints()])
        return "%s\t[%s]" % (self.id, coords)

    def getLinkDetailsAsString(self):
        """Returns detailed link attributes"""
        return "%s\t%s\t%s\t%s" % (self._id, "1", self.getStartVertex().getId(),
                                   self.getEndVertex().getId()) + 
                                   "\t%.2f\t%.6f\t%d\t%d" %
                                   (self.getLengthInFeet(),
                                    self.getSpeedInMilesPerMinute(),
                                    self.getSatFlowPCPHGPL(),
                                    self.getNumLanes()))

    def getLinkBaysAsString(self):
        """Return info about link bays one line for each bay"""
        return "\n".join(map(str, self.iterBays()))



