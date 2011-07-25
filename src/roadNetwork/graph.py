__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import logging
import sys
from itertools import chain, izip, imap
from pbCore.utils.odict import OrderedDict
from pbCore.utils.itertools2 import pairwise

from roadNetwork.vertex import Vertex
from roadNetwork.edge import Edge 
from roadNetwork.movement import Movement 
from roadNetwork.errors import GraphError, SimError

class Graph(object):

    def __init__(self, name, simStartTimeInMin,
                 simEndTimeInMin, simTimeStepInMin):

        self.simStartTimeInMin = simStartTimeInMin
        self.simEndTimeInMin = simEndTimeInMin
        self.simTimeStepInMin = simTimeStepInMin
        
        self.name = name 
        self._vertices = OrderedDict()
        self._edges = OrderedDict()
        self._maxVertexId = 0
        
    def addVertex(self, newVertex):

        if newVertex.id in self._vertices:
            raise GraphError("Vertex %s already in the network" % newVertex.id)
        self._vertices[newVertex.id] = newVertex
        if int(newVertex.id) > self._maxVertexId:
            self._maxVertexId = int(newVertex.id) 
        
    def addEdge(self, newEdge):
        
        startVertex = self.getVertex(newEdge.startVertexId)
        endVertex = self.getVertex(newEdge.endVertexId)

        if self.hasEdge(startVertex.id, endVertex.id):
            raise GraphError("Edge %s already exists" % newEdge.iid_)

        startVertex.addOutEdge(newEdge)
        endVertex.addInEdge(newEdge)

        newEdge.simStartTimeInMin = self.simStartTimeInMin
        newEdge.simEndTimeInMin = self.simEndTimeInMin
        newEdge.simTimeStepInMin = self.simTimeStepInMin

        self._edges[startVertex.id, endVertex.id] = newEdge

    def deleteEdge(self, edgeToDelete):
        
        movsToDelete1 = [mov for mov in edgeToDelete.iterOutMovements()] 
        movsToDelete2 = [mov for mov in edgeToDelete.iterInMovements()]

        for movToDelete in movsToDelete1:
            edgeToDelete.deleteOutMovement(movToDelete) 
        
        for movToDelete in movsToDelete2:
            movToDelete.inEdge.deleteOutMovement(movToDelete) 

        edgeToDelete.startVertex._deleteOutEdge(edgeToDelete)
        edgeToDelete.endVertex._deleteInEdge(edgeToDelete)

        del self._edges[edgeToDelete.startVertexId, edgeToDelete.endVertexId]

    def deleteVertex(self, vertexToDelete):

        edgesToDelete = [edge for edge in chain(vertexToDelete.iterInEdges(),
                                                vertexToDelete.iterOutEdges())]

        for edge in edgesToDelete:
            self.deleteEdge(edge) 

        del self._vertices[vertexToDelete.id] 
                             
    def iterVertices(self):
        
        return self._vertices.itervalues()

    def iterEdges(self):
        
        return self._edges.itervalues()

    def hasVertex(self, vertexId):
        
        return vertexId in self._vertices

    def hasEdge(self, startVertexId, endVertexId):
        
        return (startVertexId, endVertexId) in self._edges

    def getVertex(self, vertexId):

        try:
            return self._vertices[vertexId]
        except KeyError, e:
            raise GraphError("Vertex %s not in the graph" % vertexId)

    def getEdge(self, startVertexId, endVertexId):

        try:
            return self._edges[startVertexId, endVertexId]
        except KeyError, e:
            raise GraphError("Edge %s to %s not in the graph" % 
                                   (startVertexId, endVertexId))

    def getNumVertices(self):

        return len(self._vertices)

    def getNumEdges(self):

        return len(self._edges)

    def getNewVertexId(self):
        """Return a new regular node id that is one plus the highest node id"""
        
        return str(self._maxVertexId + 1)

    def splitEdge(self, edgeToSplit):

        upVertex = edgeToSplit.startVertex
        downVertex = edgeToSplit.endVertex 

        midX = (upVertex.x + downVertex.x) / 2
        midY = (upVertex.y + downVertex.y) / 2

        middleVertex = Vertex(self.getNewVertexId(), midX, midY)

        self.addVertex(middleVertex)
        
        iMovs = [(mov.inEdge, mov.numLanes)
                  for mov in edgeToSplit.iterInMovements()]
                 

        eMovs = [(mov.outEdge, mov.numLanes) for 
                 mov in edgeToSplit.iterOutMovements()] 

        numLanes = edgeToSplit.getNumLanes() 
        self.deleteEdge(edgeToSplit) 

        newEdge1 = Edge(upVertex, middleVertex, numLanes) 
        newEdge2 = Edge(middleVertex, downVertex, numLanes) 

        self.addEdge(newEdge1)
        self.addEdge(newEdge2)

        for upEdge, numInLanes in iMovs:
            newMovement = Movement(upEdge, newEdge1, numInLanes)
            upEdge.addOutMovement(newMovement) 

        for downEdge, numOutLanes, in eMovs:
            newMovement = Movement(newEdge2, downEdge, numOutLanes)
            newEdge2.addOutMovement(newMovement) 

        movement = Movement(newEdge1, newEdge2, numLanes) 
        newEdge1.addOutMovement(movement) 
            
        return newEdge1, newEdge2

    def _createTimeVaryingEdgeAttribute(self, attributeName):

        for edge in self.iterEdges():
            if hasattr(edge, attributeName):
                raise GraphError('Edge %s already has a an attribute named %s' % 
                                   (edge.iid_, attributeName))
            setattr(edge, attributeName, {})

    def _createTimeVaryingMovementAttribute(self, attributeName):

        for edge in self.iterEdges():
            for eMov in edge.iterOutMovements():
                if hasattr(eMov, attributeName):
                    raise GraphError("Movement %s aready has an attribute named %s" % 
                                       (eMov.iid_, attributeName))
                setattr(eMov, attributeName, {})
            
    def readTimeVaryingEdgeAttribute(self, fileName, attrName, startTimeInMin, endTimeInMin, timeStepInMin, hasHeader=True):

        assert self.simStartTimeInMin <= startTimeInMin < self.simEndTimeInMin
        assert self.simStartTimeInMin < endTimeInMin <= self.simEndTimeInMin
        assert timeStepInMin % self.simTimeStepInMin == 0

        self._createTimeVaryingEdgeAttribute(attrName)

        numTimeIntervals = len(range(startTimeInMin, endTimeInMin, timeStepInMin))

        inputStream = open(fileName, 'r')
        if hasHeader:
            inputStream.next() # this is the header 
        
        for line in inputStream:
            fields = line.strip().split(",")
            nodeAid, nodeBid = fields[:2]

            try:
                edge = self.getEdge(nodeAid, nodeBid)
            except Graph, e:
                logging.error(str(e))
                continue

            attrValue = {}
            i = 2

            if len(fields[2:]) != numTimeIntervals:
                raise Graph('The number of time intervals from %d to %d using time step %d'
                                ' are not the same as the number of columns in %s' %
                                (startTimeInMin, endTimeInMin, timeStepInMin, fileName))

            for start, end in pairwise(range(startTimeInMin, endTimeInMin + 1, timeStepInMin)):
                attrValue[start, end] = float(fields[i])
                i += 1
            setattr(edge, attrName, attrValue)
        inputStream.close()            

    def readTimeVaryingMovementAttribute(self, fileName, attrName, startTimeInMin, endTimeInMin, timeStepInMin, hasHeader=True):
        """Reads a list of values from each line in the input fileName and assigns
        each value to the corresponding time interval specified
        by the last three input arguments

        the movement attribute can be accesse as mov.attrName[startInMin, endInMin]

        """

        assert self.simStartTimeInMin <= startTimeInMin < self.simEndTimeInMin
        assert self.simStartTimeInMin < endTimeInMin <= self.simEndTimeInMin
        assert timeStepInMin % self.simTimeStepInMin == 0

        self._createTimeVaryingMovementAttribute(attrName)

        inputStream = open(fileName, 'r')
        if hasHeader:
            inputStream.next()

        numTimeIntervals = len(range(startTimeInMin, endTimeInMin, timeStepInMin))

        for line in inputStream:

            fields = line.strip().split(",")
            nodeAid, nodeBid, nodeCid = fields[0].split()

            if len(fields[1:]) != numTimeIntervals:
                raise GraphError('The number of time intervals from %d to %d using time step %d'
                                ' are not the same as the number of columns in %s' %
                                (startTimeInMin, endTimeInMin, timeStepInMin, fileName))

            attrValue = {}
            i = 1
            allValuesAreZero = True
            for start, end in pairwise(range(startTimeInMin, endTimeInMin + 1, timeStepInMin)):
                singleValue = float(fields[i])
                if singleValue != 0:
                    allValuesAreZero = False
                attrValue[start, end] = singleValue
                i += 1

            if allValuesAreZero:
                continue

            try:
                edge = self.getEdge(nodeAid, nodeBid)
                movement = edge.getOutMovement(nodeCid)

                if movement.isUTurn():
                    continue
                
            except BaseNetworkError, e:
                if nodeCid == nodeAid:
                    continue
                logging.error(str(e))
                continue
            except DynameqError, e:
                logging.error(str(e))
                continue

            setattr(movement, attrName, attrValue)
            
        inputStream.close()

    def readMovementVolumesAndTTs(self, movementFlowFileName, movementTimeFileName):
        """Read the movement travel times (in seconds) add assign them 
        to the corresponding movement"""

        inputStream1 = open(movementFlowFileName, 'r')
        inputStream2 = open(movementTimeFileName, 'r')

        numMovementsRead = 0

        for flowLine, timeLine in izip(inputStream1, inputStream2):
            
            numMovementsRead += 1 
            if numMovementsRead % 10000 == 0:
                print "Num movements read %d" % numMovementsRead

            flowFields = flowLine.strip().split()
            timeFields = timeLine.strip().split()

            nodeAid, nodeBid, nodeCid = flowFields[:3]

            if [nodeAid, nodeBid, nodeCid] != timeFields[:3]:
                raise SimError('The files %s and %s are not in sync. '
                                      'Movement through %s from %s to %s in the first file is not '
                                      'in the same line position in the second '
                                      'file' % (movementFlowFileName,
                                                movementTimeFileName,
                                                nodeBid, nodeAid, nodeCid))

            try:
                edge = self.getEdge(nodeAid, nodeBid)
                movement = edge.getOutMovement(nodeCid)
            except GraphError, e:
                if nodeAid == nodeCid:
                    continue

                logging.error(str(e))
                continue

            simFlows = imap(int, flowFields[3:])
            simTTs = imap(float, timeFields[3:])
            timePeriodStart = self.simStartTimeInMin
                    
            for simFlow, simTT in izip(simFlows, simTTs):

                if simFlow == 0 and simTT > 0:
                    raise SimError('Movement %s has zero flow in the '
                                   'time period begining %d and a '
                                   'positive travel time' % 
                                   (movement.iid, timePeriodStart))
                elif simFlow > 0 and simTT == 0:
                    simTT = 0.01
                    message = ('Movement %s has positive flow in '
                                   'the time period begining %d and a '
                                   'zero travel time. Edge length is %f' % 
                                   (movement.iid, timePeriodStart, edge.getLengthInFeet()))
                    logging.error(message)
                    #raise SimError('Movement %s has positive flow in '
                    #               'the time period begining %d and a '
                    #               'zero travel time' % 
                    #               (movement.iid, timePeriodStart))
                
                elif simFlow == 0 and simTT == 0:
                    #simTT = movement.getFreeFlowTTInMin()
                    timePeriodStart += self.simTimeStepInMin
                    if timePeriodStart >= self.simEndTimeInMin:
                        break
                else:
                    movement.setSimVolume(timePeriodStart, timePeriodStart + 
                                        self.simTimeStepInMin, simFlow)

                    movement.setSimTTInMin(timePeriodStart, timePeriodStart + 
                                          self.simTimeStepInMin, simTT) #time is in minutes! 
                                      
                    timePeriodStart += self.simTimeStepInMin
                    if timePeriodStart >= self.simEndTimeInMin:
                        break

        inputStream1.close()
        inputStream2.close()

