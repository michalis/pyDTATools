__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from algorithms.shortestPaths import ShortestPaths
from errors import GraphError

class Path(object):

    @classmethod
    def getPathFromNodes(cls, name, verticesAsList):

        assert len(verticesAsList) > 2
        
        edges = []
        curEdge = verticesAsList[0].getOutEdge(verticesAsList[1].id)
        edges.append(curEdge)
        prevVertex = curEdge.endVertex
        for vertex in verticesAsList[2:]:
            curEdge = prevVertex.getOutEdge(vertex.id)
            edges.append(curEdge)
            prevVertex = vertex 
            
        return Path(name, edges)
            
    def __init__(self, name, iterEdges):

        self._name = name

        self._edges = list(iterEdges)

        for edgeUp, edgeDown in pairwise(self._edges):
            assert edgeUp.hasOutMovement(edgeDown.endVertexId)

        if len(self._edges) == 0:
            raise GraphError("Path %s does not have any edges" % name)

        self._lengthInMiles = sum([edge.getLengthInMiles() for edge in self.iterEdges()])

        self._obsTTInMin = {}
                      
    def __repr__(self):
        
        return " ".join([vertex.id for vertex in self.iterVertices()]) 

    def __str__(self):
        
        return self.__repr__()

    def iterEdges(self):
        """Return an iterator to the edges of the route"""
        return iter(self._edges)

    def iterEdgesInReverse(self):
        """Return an iterator to the edges of the route in reverse order"""
        edges = [edge for edge in self.iterEdges]
        rEdges = edges.reverse()
        return iter(rEdges)

    def iterVertices(self):

        for edge in self.iterEdges():
            yield edge.startVertex
        yield edge.endVertex

    def getNumEdges(self):

        return len(self._edges)

    def getName(self):

        return self._name

    def getFirstVertex(self):

        return self._edges[0].startVertex

    def getLastVertex(self):

        return self._edges[-1].endVertex

    def getFirstEdge(self):

        return self._edges[0]

    def getLastEdge(self):

        return self._edges[-1]

    def getAverageSimSpeedInMPH(self, startTimeInMin, endTimeInMin):

        travelTime = self.getAverageSimTTInMin(startTimeInMin, endTimeInMin)
        return self.getLengthInMiles() / (travelTime / 60.0)
        
    def getAverageSimTTInMin(self, startTimeInMin, endTimeInMin):
        """Return the simulated travel time in minutes for the specified 
        time period using the """
        
        simTT = 0
        if self.getNumEdges() > 1:
            for upEdge, downEdge in pairwise(self.iterEdges()):
                movement = upEdge.getOutMovement(downEdge.endVertexId)
                movTT = movement.getSimTTInMin(startTimeInMin, endTimeInMin)            
                simTT += movTT
        else:
            downEdge = self._edges[0]

        if downEdge.hasThruTurn():
            finalMovement = downEdge.getThruTurn()
            movTT = finalMovement.getSimTTInMin(startTimeInMin, endTimeInMin)
            simTT += movTT
        else:
            edgeTT = downEdge.getSimTTInMin(startTimeInMin, endTimeInMin)
            simTT += edgeTT        

        return simTT

    def getLengthInMiles(self):

        return self._lengthInMiles

    def getAverageSimSpeedInMPH(self, startTimeInMin, endTimeInMin):
        
        travelTime = self.getObsTTInMin(startTimeInMin, endTimeInMin)
        return self._lengthInMiles / (travelTime / 60.0)

    def getObsTTInMin(self, startTimeInMin, endTimeInMin):
        """Get the observed travel time for the specified time period"""
        return self._obsTTInMin[startTimeInMin, endTimeInMin]

    def setObsTTInMin(self, startTimeInMin, endTimeInMin, obsTimeInMin):
        """Set the observed travel time in minutes for the specified time period"""
        self._obsTTInMin[startTimeInMin, endTimeInMin] = obsTimeInMin
        
def getSPBetweenEdges(net, pathName, listOfEdgeIds):
    """Return a path that goes through all the input edges"""

    assert len(listOfEdgeIds) >= 2

    edges = [net.getLink(edgeId) for edgeId in listOfEdgeIds]     
    ShortestPaths.initializeMovementCostsWithLengthInFeet(net)
    
    path = []
    i = 0
    for edge1, edge2 in pairwise(edges):
        ShortestPaths.labelCorrectingWithLabelsOnEdges(net, edge1)
        subPath = ShortestPaths.getShortestPathBetweenEdges(edge1, edge2)
        i += 1
        if i > 1:
            subPath.pop(0)
        path.extend(subPath) 
        
    return Path(pathName, path)
        
def getSPBetweenVertices(net, pathName, sourceVertexId, destVertexId):

    sourceVertex = net.getVertex(sourceVertexId)
    destVertex = net.getVertex(destVertexId)
    ShortestPaths.initializeEdgeCostsWithFFTT(net)
    
    ShortestPaths.labelCorrecting(net, sourceVertex)
    path = ShortestPaths.getShortestPathAsListOfEdges(sourceVertex, destVertex)
    return Path(pathName, path)
