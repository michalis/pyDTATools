__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import logging
from itertools import imap,chain
from math import fabs, atan, atan2, pi, sqrt, acos, sin, cos
import random
import sys

from roadNetwork.edge import Edge
from roadNetwork.errors import GraphError

class Vertex(object):

    def __init__(self, id_, x, y):
        
        self.id = id_
        self.iid = self.id
        self.x = x
        self.y = y        
        self._emanatingEdges = []
        self._incidentEdges = []
        self._edgesClockwise = []
                        
    def __str__(self):

        return "%s\t%f\t%f" % (self.id, self.x, self.y)

    def addOutEdge(self, edge):
        """Add the emanating instance of Edge (or subclass) instance to the list 
        of emanating links"""

        if not edge.startVertex.id == self.id:
            raise GraphError("Edge %s does not start from vertex %s" % (edge.iid_, self.id))

        if edge in self._emanatingEdges:
            raise GraphError("Edge %s already emanates from the vertex %s" % 
                            (edge.iid_, self.id))
            
        #identify the position to insert the edge
        position = 0
        for i, emanatingEdge in enumerate(self.iterOutEdges()):
            if edge.isClockwise(emanatingEdge):
                position = i + 1
        self._emanatingEdges.insert(position, edge)
        self._edgesClockwise = sorted(chain(self._incidentEdges, 
                                            self._emanatingEdges),
                          key = lambda e: self.getOrientation(e.midpoint2))

    def addInEdge(self, edge):
        """Add the incident instance of Edge (or subclass) to the list
        of incident edges"""
        
        if not edge.endVertex.id == self.id:
            raise GraphError("Edge %s does not end to vertex %s" % (edge.iid_, self.id))

        if edge in self._incidentEdges:
            raise GraphError("Edge %s is laready incident to vertex %s" % 
                            (edge.iid, self.id))

        
        position = 0
        for i, incidentEdge in enumerate(self.iterInEdges()):
            if edge.isCounterClockwise(incidentEdge):
                position = i + 1

        self._incidentEdges.insert(position, edge)
        self._edgesClockwise = sorted(chain(self._incidentEdges, 
                                            self._emanatingEdges),
                          key = lambda e: self.getOrientation(e.midpoint2))


    def _sortEdges(self):
        """Sorts the edges clockwise"""
        self._edgesClockwise = sorted(chain(self._incidentEdges, 
                                            self._emanatingEdges),
                          key = lambda e: self.getOrientation(e.midpoint2))        
                   
    def _deleteOutEdge(self, edge):
        
        #raise Exception("Not implemented yet")
        if edge not in self._emanatingEdges:
            raise GraphError("Link %s does not emanate from node %s" %
                            (edge.iid, self.id))

        self._emanatingEdges.remove(edge)
        self._sortEdges()

    def _deleteInEdge(self, edge):

        #raise Exception("Not implemented yet")
        assert isinstance(edge, Edge)

        if edge not in self._incidentEdges:
            raise GraphError("Edge %s is not incident to node %s" %
                            (edge.iid, self.id))
        
        self._incidentEdges.remove(edge)
        self._sortEdges()
    
    def getCardinality(self):

        return (self.getNumOutEdges(),
                self.getNumInEdges())
    
    def getNumOutEdges(self):

        return len(self._emanatingEdges)

    def getNumInEdges(self):

        return len(self._incidentEdges)

    def getNumAdjacentEdges(self):
        
        return len(self._emanatingEdges) + len(self._incidentEdges)

    def getNumAdjacentVertices(self):

        return sum([1 for e in self.iterAdjacentVertices()])

    def getNumPredecessorVertices(self):

        return self.getNumInEdges()

    def getNumSuccessorVertices(self):

        return self.getNumOutEdges()
    
    def getOutEdgeClockwise(self, emanatingEdge):
        
        if self.getNumOutEdges() == 0:
            raise GraphError("The vertex %s does not have any emanating edges associated with it" %
                              self.id)

        if self.getNumOutEdges() == 1:
            raise GraphError("The vertex %s has only one emanating edges associated with it" %
                              self.id)            
                              
        index = self._emanatingEdges.index(emanatingEdge)
        if index == len(self._emanatingEdges) - 1:
            return self._emanatingEdges[0]
        else:
            return self._emanatingEdges[index + 1]

    def getInEdgeClockwise(self, edge):

        if self.getNumInEdges() == 0:
            raise GraphError("The vertex %s does not have any incident edges associated with it" %
                              self.id)
        
        if self.getNumInEdges() == 1:
            raise GraphError("The vertex %s has only one incident edge associated with it" %
                              self.id)

        index = self._incidentEdges.index(edge)
        if index == 0:
            return self._incidentEdges[-1]
        else:
            return self._incidentEdges[index - 1]
                
    def getInEdgeCounterClockwise(self, edge):
        
        if self.getNumInEdges() == 0:
            raise GraphError("The vertex %s does not have any incident edges associated with it" %
                              self.id)
        
        if self.getNumInEdges() == 1:
            raise GraphError("The vertex %s has only one incident edge associated with it" %
                              self.id)
            
        index = self._incidentEdges.index(edge)
        
        if index == len(self._incidentEdges) - 1:
            return self._incidentEdges[0]
        else:
            return self._incidentEdges[index + 1]
        
    def getEdgeClockwise(self, edge):
        """Get the closest edge either incident or emanating that is
        the first edge to encounter if you are to start walking
        clockwise from this edge"""
        

        # assign mate links to be the pairs of incident/emanating links 
        #that have a difference of angle that is less than 5degrees

        #now if there is an incident or emanating link without a mate
        #then you should shift it to the left or right. 
        
        #now every edge has the left and right edge based on the offset 
        
        #how do pick the next link? you just pick the next link with 
        #the smallest angle 
        #so you need the angle between three points  nodeA, self, nodeB

        #sort by angle
        #allEdges = sorted(chain(self._incidentEdges, self._emanatingEdges),
        #                  key = lambda e: self.getOrientation(e.midpoint2))

        allEdges = self._edgesClockwise 
        index = allEdges.index(edge)
        if index != len(allEdges) - 1:
            return allEdges[index + 1]
        else:
            return allEdges[0]
        
    def getOutEdge(self, vertexId):
        
        for edge in self.iterOutEdges():
            if edge.endVertexId == vertexId:
                return edge
        
        raise GraphError("Vertex %s is not connected to vertex %s" % (self.id ,vertexId))

    def getInEdge(self, vertexId):
                               
        for edge in self.iterInEdges():
            if edge.startVertexId == vertexId:
                return edge 
        raise GraphError("Vertex %s is not connected to vertex %s" % (vertexId, self.id))

    def getMovement(self, upVertexId, downVertexId):
        
        iEdge = self.getInEdge(upVertexId)
        mov = iEdge.getOutMovement(downVertexId) 
        return mov
        
    def getNumMovements(self):
        """Return the number of permitted movements through the intersection"""
        return sum(imap(lambda mov:1, self.iterMovements()))
        
    def hasOutEdge(self, vertexId):

        return vertexId in [edge.endVertex.id for edge in self.iterOutEdges()]

    def hasInEdge(self, vertexId):

        return vertexId in [edge.startVertexId for edge in self.iterInEdges()]

    def hasMovement(self, upVertexId, downVertexId):
        
        for mov in self.iterMovements():
            if mov.startVertexId == upVertexId and mov.vertexCid == downVertexId:
                return True
        return False 

    def iterMovements(self):

        return (mov for iEdge in self.iterInEdges() for mov in iEdge.iterOutMovements())  

    def iterEdgesClockwise(self):

        return iter(self._edgesClockwise)

    def iterEdgePairs(self):

        if self.getNumAdjacentEdges() < 2:
            raise GraphError("Number of adjacent edges is less than 2") 

        if self.getNumAdjacentEdges() == 2:
            yield self._edgesClockwise[0], self._edgesClockwise[1]
            raise StopIteration

        eIter = self.iterEdgesClockwise()
        edge1 = eIter.next()
        while True:
            try:
                edge2 = eIter.next() 
                yield (edge1, edge2)
                edge1 = edge2 

            except StopIteration:
                yield self._edgesClockwise[-1], self._edgesClockwise[0] 
                raise StopIteration 
                        
    def iterOutEdges(self):

        return iter(self._emanatingEdges)

    def iterInEdges(self):

        return iter(self._incidentEdges)

    def iterSuccVertices(self):

        for edge in self.iterOutEdges():
            yield edge.endVertex

    def iterPredVertices(self):

        for edge in self.iterInEdges():
            yield edge.startVertex

    def iterAdjacentVertices(self):
         
        av = set(self.iterSuccVertices())
        av = av.union(set(self.iterPredVertices()))
        return iter(av)
        
    def iterEdges(self):

        return chain(self.iterOutEdges(), self.iterInEdges())

    def isJunction(self):
        
        if self.getNumOutEdges() == 1 or self.getNumInEdges() == 1:
            return True
        return False

    def isShapePoint(self):

        if self.getNumAdjacentEdges() == 4 and self.getNumAdjacentVertices() == 2:
            return True
        if self.getNumAdjacentEdges() == 2 and self.getNumAdjacentVertices() == 2:
            return True
        return False

    def isIntersection(self):
        
        return not self.isJunction()

    def isIncoming(self, edge):

        return True if edge in self._incidentEdges else False

    def isOutgoing(self, edge):

        return True if edge in self._emanatingEdges else False 
    
    def getOrientation(self, point):

        x1 = self.x
        y1 = self.y
        x2 = point.x
        y2 = point.y

        if x2 > x1 and y2 <= y1:   # 2nd quarter
            orientation = atan(fabs(y2-y1)/fabs(x2-x1)) + pi/2
        elif x2 <= x1 and y2 < y1:   # 3th quarter
            orientation = atan(fabs(x2-x1)/fabs(y2-y1)) + pi
        elif x2 < x1 and y2 >= y1:  # 4nd quarter 
            orientation = atan(fabs(y2-y1)/fabs(x2-x1)) + 3 * pi/2
        elif x2 >= x1 and y2 > y1:  # 1st quarter
            orientation = atan(fabs(x2-x1)/fabs(y2-y1))
        else:
            orientation = 0.0

        return orientation * 180.0 / pi

                        
