__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from itertools import izip
from math import fabs, atan, atan2, pi, sqrt, acos, sin, cos
import logging
from collections import defaultdict
from math import sqrt

from roadNetwork.point import Point
from roadNetwork.movement import Movement
from roadNetwork.errors import GraphError, SimError

from pbCore.utils.itertools2 import pairwise


class Edge(object):

    def __init__(self, startVertex, endVertex, numLanes, shape=None):

        self.iid = (startVertex.id, endVertex.id)        
        self.iid_ = "%s %s" % self.iid

        self.startVertexId = startVertex.id
        self.endVertexId = endVertex.id
        
        self.startVertex = startVertex
        self.endVertex = endVertex
        self._numLanes = numLanes
        
        self._shape = shape

        self.numLanes = numLanes 
        
        self._outMovements = []
        self._inMovements = []
        
        #TODO: you need to offset the point 
        self.midpoint2 = Point((self.startVertex.x + self.endVertex.x) / 2.0,
                               (self.startVertex.y + self.endVertex.y)/ 2.0)

        self._obsCount = {}
        self._simVolume = defaultdict(int)
        self._simMeanTT = defaultdict(float)

        self.lengthInFeet = sqrt((self.endVertex.x - self.startVertex.x)**2 +
                                 (self.endVertex.y - self.startVertex.y)**2)

        self.lengthInMiles = self.lengthInFeet / 5280.0
        self.freeFlowSpeedInMPH = 50.0

        self.simStartTimeInMin = None
        self.simEndTimeInMin = None
        self.simTimeStepInMin = None


                        
    def __str__(self):

        return self.iid_
            
    def addOutMovement(self, newMovement):

        if not isinstance(newMovement, Movement):
            raise GraphError("Please provide an instance of BaseNetwork.Movement as an input argument")

        if self.endVertexId != newMovement.vertexId:
            raise GraphError("Edges %s and %s are not consecutive" % (self.iid_,
                                                                     newMovement.outEdge.iid_))

        if self.hasOutMovement(newMovement.outVertexId):
            raise GraphError("Movement from %s to %s and %s already exists" %
                            (self.startVertexId, self.endVertexId, newMovement.outVertexId))

        if newMovement.numLanes <= 0:
             raise GraphError("The number of lanes: %d of the new movement %s %s must be positive"
                                   % (newMovement.numLanes, self.iid_, newMovement.outVertexId))           

        position = 0
        for eMov in self.iterOutMovements():
            if newMovement.outEdge.isClockwise(eMov.outEdge):
                position += 1
        self._outMovements.insert(position, newMovement)

        #all the incident movements are sorted anti clockwise
        position = 0
        for iMov in newMovement.outEdge.iterInMovements():
            if self.isCounterClockwise(iMov.inEdge):
                position += 1
                
        newMovement.outEdge._inMovements.insert(position, newMovement)

        newMovement.simStartTimeInMin = self.simStartTimeInMin
        newMovement.simEndTimeInMin = self.simEndTimeInMin
        newMovement.simTimeStepInMin = self.simTimeStepInMin

    def deleteOutMovement(self, movement):
        #TODO: what if I handle this at he vertex level???? 
        #I think it would be better to handle it at the vertex level 
        #and delete lane connection at the movement level 
        if not movement.inEdge == self:
            raise GraphError("Movement %s does not emanate from edge %s" %
                                   (movement.iid_, self.iid_))

        if not self.hasOutMovement(movement.outVertexId):
            raise GraphError("Movement %s does not exist" % movement.iid_)
        
        self._outMovements.remove(movement)
        movement.outEdge._inMovements.remove(movement)
    
    def hasOutMovement(self, downstreamVertexId):
        
        for eMov in self.iterOutMovements():
            if eMov.outVertexId == downstreamVertexId:
                return True
        return False

    def hasInMovement(self, upstreamVertexId):

        for iMov in self.iterInMovements():
            if iMov.inVertexId == upstreamVertexId:
                return True
        return False

    def hasLeftTurn(self):

        for oMov in self.iterOutMovements():
            if oMov.isLeftTurn():
                return True
        return False

    def hasRightTurn(self):

        for oMov in self.iterOutMovements():
            if oMov.isRightTurn():
                return True
        return False

    def hasThruTurn(self):

        for oMov in self.iterOutMovements():
            if oMov.isThruTurn():
                return True
        return False

    def getCrossStreetNameAtStart(self):
        #TODO: should it throw?
        if self.getStreetName():
            for mov in self.iterInMovements():
                if mov.inEdge.getStreetName() != self.getStreetName():
                    return mov.inEdge.getStreetName()
        return ""

    def getCrossStreetNameAtEnd(self):
        #TODO: should it throw instead?
        if self.getStreetName():
            for mov in self.iterOutMovements():
                if mov.outEdge.getStreetName() != self.getStreetName():
                    return mov.outEdge.getStreetName()
        return ""

    def getLeftTurn(self):

        for mov in self.iterOutMovements():
            if mov.isLeftTurn():
                return mov
        raise GraphError("Edge %s has no left turn" % edge.iid_)

    def getThruTurn(self):

        for mov in self.iterOutMovements():
            if mov.isThruTurn():
                return mov
        raise GraphError("Edge %s has no thru turn" % edge.iid_)

    def getRightTurn(self):

        for mov in self.iterOutMovements():
            if mov.isRightTurn():
                return mov
        raise GraphError("Edge %s has no right turn" % edge.iid_) 

    def getFreeFlowSpeedInMPH(self):

        return self.freeFlowSpeedInMPH

    def getLengthInMiles(self):

        return self.lengthInMiles

    def getNumLanes(self):

        return self.numLanes
    
    def getOutMovement(self, downstreamVertexId):

        for movement in self.iterOutMovements():
            if movement.outVertexId == downstreamVertexId:
                return movement
        raise GraphError("Edge %s does not have an emanating movement towards %s"
                               % (self.iid_, downstreamVertexId))

    def getNumOutMovements(self):

        return len(self._outMovements)

    def getNumInMovements(self):
        
        return len(self._inMovements)
            
    def iterOutMovements(self):
        
        return iter(self._outMovements)

    def iterInMovements(self):
        
        return iter(self._inMovements)

    def isClockwise(self, other):
        """Return true if you turn clockwise to get to the other edge"""

        if self == other:
            raise GraphError("Same Edges")

        #two emanatingEdges
        if self.startVertex == other.startVertex:
            p0 = self.endVertex
            p1 = self.startVertex
            p2 = other.endVertex 
        #two incident edges
        elif self.endVertex == other.endVertex:
            p0 = self.startVertex
            p1 = self.endVertex
            p2 = other.startVertex
        #if I am incident and the other emanating
        elif self.endVertex == other.startVertex:
            p0 = self.startVertex
            p1 = self.endVertex
            p2 = other.endVertex
        elif self.startVertex == other.endVertex:
            p0 = self.endVertex
            p1 = self.startVertex
            p2 = other.startVertex 
        else:
            raise GraphError("Something went wrong in the classification of edges")

        if getTurnType(p0, p1, p2) == TurnType.clockwise:
            return True
        else:
            return False
        
    def isCounterClockwise(self, other):
        """Return tru if you turn counter clockwise to get to the other edge. 
        But they may also be collinear"""
        return not self.isClockwise(other)

    def getAcuteAngle(self, other):

        #TODO: this is a simple copy what is in the isClockwise method  
        #two emanatingEdges
        if self.startVertex == other.startVertex:
            p0 = self.endVertex
            p1 = self.startVertex
            p2 = other.endVertex 
        #two incident edges
        elif self.endVertex == other.endVertex:
            p0 = self.startVertex
            p1 = self.endVertex
            p2 = other.startVertex
        #if I am incident and the other emanating
        elif self.endVertex == other.startVertex:
            p0 = self.startVertex
            p1 = self.endVertex
            p2 = other.endVertex
        elif self.startVertex == other.endVertex:
            p0 = self.endVertex
            p1 = self.startVertex
            p2 = other.startVertex 
        else:
            raise GraphError("Something went wrong in the classification of edges")
        
        dx1 = p0.x - p1.x
        dy1 = p0.y - p1.y
        dx2 = p2.x - p1.x
        dy2 = p2.y - p1.y

        length1 = sqrt(dx1 ** 2 + dy1 ** 2)
        length2 = sqrt(dx2 ** 2 + dy2 ** 2)

        return abs(acos((dx1 * dx2 + dy1 * dy2) / (length1 * length2))) / pi * 180.0

    def getAngleClockwise(self, other):
        """Get the angle between the two edges measured
        clockwise. Rotate the other edge clockwise until it hits this one"""

        dx1 = self.endVertex.x - self.startVertex.x 
        dy1 = self.endVertex.y - self.startVertex.y 

        dx2 = other.endVertex.x - other.startVertex.x 
        dy2 = other.endVertex.y - other.startVertex.y 
        
        angle = (atan2(dy2, dx2) - atan2(dy1, dx1)) * 180 / pi
        if angle < 0:
            angle += 360
        return angle    

    def getOrientation(self):
        """Returs the orientation of the link in degrees from the North
        measured clockwise. Only the endpoints are used in the calculation"""

        x1 = self.startVertex.x
        y1 = self.startVertex.y
        x2 = self.endVertex.x
        y2 = self.endVertex.y

        #TODO: why the following does not work? 
        #return atan2(y2 -y1, x2 - x1) * 180 / pi        
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

    def _validateInputTimes(self, startTimeInMin, endTimeInMin):
        """Checks that the input times belong to the simulation window"""
        if startTimeInMin >= endTimeInMin:
            raise SimError("Invalid time bin (%d %s). The end time cannot be equal or less "
                                "than the end time" % (startTimeInMin, endTimeInMin))

        if startTimeInMin < self.simStartTimeInMin or endTimeInMin > \
                self.simEndTimeInMin:
            raise SimError('Time period from %d to %d is out of '
                                   'simulation time' % (startTimeInMin, endTimeInMin))

    def _checkInputTimeStep(self, startTimeInMin, endTimeInMin):
        """Checks if the difference of the input times is equal to the simulation time step"""
        #TODO which check should I keep
        if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
            raise SimError('Time period from %d to %d is not '
                                   'is not in multiple simulation '
                                   'time steps %d' % (startTimeInMin, endTimeInMin,
                                                    self.simTimeStepInMin))
            
    def _checkOutputTimeStep(self, startTimeInMin, endTimeInMin):
        """Check that the difference of the input times is in multiples of the simulation time step"""
        if (endTimeInMin - startTimeInMin) % self.simTimeStepInMin != 0:
            raise SimError('Time period from %d to %d is not '
                                   'is not in multiple simulation '
                                   'time steps %d' % (startTimeInMin, endTimeInMin,
                                                    self.simTimeStepInMin))


    def _hasAllMovementCounts(self, startTimeInMin, endTimeInMin):
        """Return True if all the movements have counts"""
        count = self._aggregateAllMovementCounts(startTimeInMin, endTimeInMin)
        return True if count else False

    def _hasMovementVolumes(self, startTimeInMin, endTimeInMin):
        """Return True if at least one movement has a volume 
        greater than 0"""
        for mov in self.iterOutMovements():
            if mov.getSimVolume(startTimeInMin, endTimeInMin) > 0:
                return True
        return False

    def _aggregateAllMovementCounts(self, startTimeInMin, endTimeInMin):
        """Aggregate all the emanating movement counts of this edge
        If a count is missing return None"""
        linkCount = 0
        for movement in self.iterOutMovements():
            if movement.isUTurn():
                continue
            count = movement.getObsCount(startTimeInMin, endTimeInMin)
            #TODO a movement can return a zero value!!! so if you say
            #if count you are missing many movements
            if count is not None:
                linkCount += count
            else:
                return None
        #TODO: is this right???
        return linkCount if linkCount else None

    def getSimFlow(self, startTimeInMin, endTimeInMin):
        """Get the simulated flow in vph"""
        volume = self.getSimVolume(startTimeInMin, endTimeInMin)        
        return int(float(volume) / (endTimeInMin - startTimeInMin) * 60)

    def getSimVolume(self, startTimeInMin, endTimeInMin):
        """Return the volume on the link from startTimeInMin to endTimeInMin"""

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if self.getNumOutMovements() > 0:
            return sum([mov.getSimVolume(startTimeInMin, endTimeInMin) 
                        for mov in self.iterOutMovements()])
        else:
            result = 0
            for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                                 self.simTimeStepInMin)):
                result += self._simVolume[stTime, enTime]
            return result

    def getSimTTInMin(self, startTimeInMin, endTimeInMin):
        """Get the average travel time of the vehicles traversing the link"""

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        start = startTimeInMin
        end = endTimeInMin

        totalFlow = self.getSimVolume(start, end)
        if totalFlow == 0:
            return self.getFreeFlowTTInMin()

        if not self._simMeanTT and not self._simVolume:
            totalTime = sum([ mov.getSimTTInMin(start, end) * mov.getSimVolume(start, end)
                          for mov in self.iterOutMovements()])
            return totalTime / float(totalFlow)
        elif self._simMeanTT and self._simVolume:
            totalTime = 0
            totalFlow = 0
            for (stTime, enTime), flow in self._simVolume.iteritems():
                if stTime >= startTimeInMin and enTime <= endTimeInMin:

                    binTT = self._simMeanTT[(stTime, enTime)]

                    if flow == 0 and binTT == 0:
                        continue
                    elif flow > 0 and binTT > 0:
                        totalFlow += flow
                        totalTime += binTT * flow
                    else:                        
                        raise SimMovementError("Movement %s has flow: %f and TT: %f "
                                               "for time period from %d to %d"  % 
                                               (self.iid, flow, binTT, 
                                                startTimeInMin, endTimeInMin))

            return totalTime / float(totalFlow)
            
            if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
                raise SimError("Not implemeted yet")

            return self._simMeanTT[start, end]
        else:
            return self.lengthInMiles / float(self.freeFlowSpdInMPH) * 60

    def getSimSpeedInMPH(self, startTimeInMin, endTimeInMin):

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)
        
        #TODO if the coordinate system is not in feet 
        # you are going to have a problem
        tt = self.getSimTTInMin(startTimeInMin, endTimeInMin)
        speedInMPH = self.getLengthInMiles() / (tt / 60.)
        return speedInMPH

    def getObsCount(self, startTimeInMin, endTimeInMin):

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        allMovementCounts = self._aggregateAllMovementCounts(startTimeInMin, endTimeInMin)
        if allMovementCounts:
            return allMovementCounts
        else:
            result = 0
            simTimeStep = self.simTimeStepInMin
            if not simTimeStep:
                raise SimError("To return a count you need to set the simulation time step")

            if (startTimeInMin, endTimeInMin) in self._obsCount:
                return self._obsCount[startTimeInMin, endTimeInMin]

            for i in range((endTimeInMin - startTimeInMin) / simTimeStep):
                multipleOfSimTimeStep = (i + 1) * simTimeStep
                result = 0
                for startTime, endTime in pairwise(range(startTimeInMin, endTimeInMin + 1, multipleOfSimTimeStep)):
                    try:
                        result += self._obsCount[startTime, endTime]
                    except KeyError:
                        result = 0
                        break
                else:
                    return result

            return result if result > 0 else None
            
    def getObsMeanTT(self, startTimeInMin, endTimeInMin):
        """Get the observed mean travel time of the link in minutes"""
        raise Exception("Not implemented yet")
        return self._obsMeanTT[startTimeInMin, endTimeInMin]
            
    def getObsSpeedInMPH(self, startTimeInMin, endTimeInMin):
        """Get the observed speed of specified time period"""
        raise Exception("Not implemented yet")
        return self._obsSpeed[startTimeInMin, endTimeInMin]

    def hasMovementCountInfo(self):
        """Return true if one or more of the emanating movements 
        contain count info"""

        for eMov in self.iterOutMovements():
            if eMov.hasCountInfo():
                return True
        return False

    def hasCountInfo(self):
        """Return True if the edge has count info specific to the edge 
        or if all its emanating movements (except the uturns) have 
        a count info"""

        if len(self._obsCount) > 0:
            return True

        if self.getNumOutMovements() == 0:
            return False

        if self.getNumOutMovements() == 1:
            for mov in self.iterOutMovements():
                if mov.isUTurn():
                    return False
            
        for eMov in self.iterOutMovements():
            if eMov.isUTurn():
                continue
            if not eMov.hasCountInfo():
                return False
        return True
                    
    def hasObsCount(self, startTimeInMin, endTimeInMin):
        """Return True if the link there is count for the supplied
        time period otherwise return false"""
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        return True if self.getObsCount(startTimeInMin, endTimeInMin) else False

    def iterVehicles(self, startTimeInMin, endTimeInMin):
        """Return an iterator to all the vehicles that leave the edge in the 
        input time period"""
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if self.getNumOutMovements() == 0:
            result = []
            for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                                 self.simTimeStepInMin)):
                result.append(self._vehicles[stTime, enTime])

            return chain(*result)
        else:            
            return chain(*[mov.iterVehicles(startTimeInMin, endTimeInMin) for mov in 
                         self.iterOutMovements()])
            
    def iterCountPeriods(self, timeStepInMin=None):
        """Return an iterator to the time periods the links has counts. A time 
        period is a tuple of (startTimeInMin, endTimeInMin)"""
        if not timeStepInMin:
            if self._obsCount:
                for start, end in  sorted(self._obsCount.iterkeys()):
                    yield (start, end)
            countPeriods = set()
            for movement in self.iterOutMovements():
                for countPeriod in movement.iterCountPeriods():
                    countPeriods.add(countPeriod)
            for start, end in iter(sorted(countPeriods)):
                yield (start, end)
        else:
            if self._obsCount:
                minTime = min(self._obsCount.keys())[0]
                maxTime = max(self._obsCount.keys())[1]
                for start, end in pairwise(range(minTime, maxTime + 1, timeStepInMin)):
                    yield (start, end)
            else:
                countPeriods = set()
                for movement in self.iterOutMovements():
                    for countPeriod in movement.iterCountPeriods():
                        countPeriods.add(countPeriod)
                minTime = min(countPeriods)[0]
                maxTime = max(countPeriods)[1]
                for start, end in pairwise(range(minTime, maxTime + 1, timeStepInMin)):
                    yield (start, end)
               
    def iterCounts(self):
        """Return an iterator to the link counts. Returned values 
        have the form (start, end), count"""

        if self._obsCount:
            for period in sorted(self._obsCount.keys()):
                if self._obsCount[period]:
                    yield period, self._obsCount[period]        
        else:
            for start, end in self.iterCountPeriods():
                count = self.getObsCount(start, end)
                if count:
                    yield (start, end), count
    
    def setObsCount(self, startTimeInMin, endTimeInMin, count):
        """Specify the number of vehicles executing the movement 
        in the supplied time period
        """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if count < 0:
            raise SimError('Count for time period from %d to %d cannot be '
                                   'negative' % (startTimeInMin, endTimeInMin))
        if self._hasAllMovementCounts(startTimeInMin, endTimeInMin):
            message = ('Edge %s has has obs count from its movements from %d to %d equal to %d. '
                        'Edge count %d is ignored'
                        % (str(self.iid), startTimeInMin, endTimeInMin,
                self.getObsCount(startTimeInMin, endTimeInMin), count))
            logging.error(message)
            raise SimError(message)

        self._obsCount[startTimeInMin, endTimeInMin] = count
    
    def setSimVolume(self, startTimeInMin, endTimeInMin, volume):
        """Set the simulated volume on the edge provided that the edge 
        does not have any emanating movements"""
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        if self._hasMovementVolumes(startTimeInMin, endTimeInMin):
            raise SimError('Cannoot set the simulated volume on the edge %s'
                               'because there is at least one emanating '
                               'movement with volume greater than zero ' %
                               str(self.iid))

        if self.getNumOutMovements() > 1:
            raise SimError('Cannot set the simulated volume of the edge %s'
                               'with one or more emanating movements. Please'
                               ' set the volume of the movements' % str(self.iid))
        elif self.getNumOutMovements() == 1:
            for emanatingMovement in self.iterOutMovements():
                emanatingMovement.setSimVolume(startTimeInMin, endTimeInMin, volume)
        else:
            self._simVolume[startTimeInMin, endTimeInMin] = volume
        
    def setSimTTInMin(self, startTimeInMin, endTimeInMin, averageTTInMin):

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        if startTimeInMin < self.simStartTimeInMin or endTimeInMin > \
                self.simEndTimeInMin:
            raise SimError('Time period from %d to %d is out of '
                                   'simulation time' % (startTimeInMin, endTimeInMin))

        if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
            raise SimError('Not implemetd yet. Time period is different than the time step.')


        if self.getNumOutMovements() > 1:
            raise SimError('Cannot set the simulated travel time of the edge %s'
                               'with one or more emanating movements. Please'
                               ' set the time of the movements instead' % str(self.iid))
        elif self.getNumOutMovements() == 1:
            if averageTTInMin == 0:
                return
            for emanatingMovement in self.iterOutMovements():
                emanatingMovement.setSimTTInMin(startTimeInMin, endTimeInMin, averageTTInMin)
        else:
            if averageTTInMin == 0:
                return
            if self.getSimVolume(startTimeInMin, endTimeInMin) == 0:
                raise SimError('Cannot set the travel time on edge %s because it has zero flow' % self.iid_)

            self._simMeanTT[startTimeInMin, endTimeInMin] = averageTTInMin
    

class TurnType(object):
    
    __slots__ = () 

    counterClockwise, clockwise, collinear = (1, -1, 0)


def getTurnType(p0, p1, p2):

    """        
                {  1 if the turn from p0 to p1 to p2 is counter-clockwise.
                { -1 if the turn from p0 to p1 to p2 is clockwise.
        return  { -1 if the points are collinear and p0 is in the middle.
                {  1 if the points are collinear and p1 is in the middle.
                {  0 if the points are collinear and p2 is in the middle.

    """


    dx1 = p1.x - p0.x
    dy1 = p1.y - p0.y
    dx2 = p2.x - p0.x
    dy2 = p2.y - p0.y
    
    if dy1 * dx2 < dy2 * dx1:
        return TurnType.counterClockwise
    if dy1 * dx2 > dy2 * dx1:
        return TurnType.clockwise
    if dx1 * dx2 < 0 or dy1 * dy2 < 0:
        return TurnType.counterClockwise
    if sqrt(abs(dx1)) + sqrt(abs(dy1)) >= sqrt(abs(dx2)) + sqrt(abs(dy2)):
        return TurnType.collinear
    else:
        return TurnType.clockwise


