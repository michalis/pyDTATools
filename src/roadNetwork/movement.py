__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from collections import defaultdict

from roadNetwork.errors import GraphError, SimError

from pbCore.utils.itertools2 import pairwise

class MovementType(object):
    
    __slots__ = ()

    UT, LT2, LT, TH, RT, RT2 = range(6)

class Movement(object):
    """Represents a movement between two subsequent network edges.
    Is defined/consists by one or more lane connections. 
    """

    def __init__(self, inEdge, outEdge, numLanes):

        self.iid = (inEdge.startVertexId, 
                    inEdge.endVertexId, 
                    outEdge.endVertexId) 
        self.iid_ = '%s %s %s' % (inEdge.startVertexId, 
                                  inEdge.endVertexId, 
                                  outEdge.endVertexId) 

         
        if (inEdge.endVertex != outEdge.startVertex):
            raise GraphError("Edge %s cannot have a movement towards edge %s" %
                             (inEdge.iid_, outEdge.iid_))
        
        self.inEdge = inEdge
        self.outEdge = outEdge         

        self.inVertex = inEdge.startVertex
        self.vertex = inEdge.endVertex
        self.outVertex = outEdge.endVertex

        self.inVertexId = self.inVertex.id
        self.vertexId = self.vertex.id
        self.outVertexId = self.outVertex.id

        self.numLanes = numLanes

        self.simTimeStepInMin = None
        self.simStartTimeInMin = None
        self.simEndTimeInMin = None

        self._simVolume = defaultdict(int)   # indexed by timeperiod
        self._obsCount = {}
        self._simMeanTT = defaultdict(float)                   # indexed by timeperiod
        self._timeVaryingCosts = []
        self._penalty = 0
        
             
        self.baseTurnType = self.getTurnType()

    def __str__(self):

        return "%s %s %s %d" % (self.upVertexid, self.vertexBid,
                                self.vertexCid, self.numLanes)

    def getTurnType(self):
        """Return the type of turn the movement corresponds to based 
        on the angle it forms"""
        angle = self.inEdge.getAngleClockwise(self.outEdge)

        if self.isUTurn():
            return MovementType.UT
        elif 135 <= angle < 180:
            return MovementType.LT2
        elif 45 <= angle < 135:
            return MovementType.LT
        elif 0 <= angle  < 45:
            return MovementType.TH
        elif 315 <= angle < 360:
            return MovementType.TH
        elif 225 <= angle < 315:
            return MovementType.RT
        else:
            return MovementType.RT2
        
    def getUpstreamEdge(self):
        
        return self.inEdge

    def getDownStreamEdge(self):
        
        return self.outEdge

    def getNumLanes(self):
        
        return self._numLanes
    
    def isRightTurn(self):
        """Return True if the movement is a right turn"""
        if self._turnType == MovementType.RT or self._turnType == MovementType.RT2:
            return True
        return False 

    def isLeftTurn(self):
        """Return True if the movmenet is a left turn"""
        if self._turnType == MovementType.LT or self._turnType == MovementType.LT2:
            return True
        return False 

    def isThruTurn(self):
        """Return True if the movement is a through movement"""
        return True if self._turnType == MovementType.TH else False 
                                    
    def isUTurn(self):
        """Return True if it is a UTurn and False otherwise"""
        return True if self.inVertexId == self.outVertexId else False 

    def isConflicting(self, other):
        """Return true if the two movements are conflicting 
        false otherwise"""
        raise GraphError('Not implemented yet')
        

    def _checkInputTimeStep(self, startTimeInMin, endTimeInMin):
        """The input time step should always be equal to the sim time step"""
        if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
            raise SimError('Time period from %d to %d is not '
                                   'equal to the simulation time step %d'
                                   % (startTimeInMin, endTimeInMin, 
                                      self.simTimeStepInMin))
            
    def _checkOutputTimeStep(self, startTimeInMin, endTimeInMin):
        """Checks that the difference in the input times is in multiples 
        of the simulation time step"""
        if (endTimeInMin - startTimeInMin) % self.simTimeStepInMin != 0:
            raise SimError('Time period from %d to %d is not '
                                   'is a multiple of the simulation time step ' 
                                    '%d' % (startTimeInMin, endTimeInMin,
                                                    self.simTimeStepInMin))


    def _validateInputTimes(self, startTimeInMin, endTimeInMin):
        """Checks that the start time is less than the end time and that both 
        times are in the simulation time window"""
        
        if startTimeInMin >= endTimeInMin:
            raise SimError("Invalid time bin (%d %s). The end time cannot be equal or less "
                                "than the end time" % (startTimeInMin, endTimeInMin))

        if startTimeInMin < self.simStartTimeInMin or endTimeInMin > \
                self .simEndTimeInMin:
            raise SimError('Time period from %d to %d is out of '
                                   'simulation time' % (startTimeInMin, endTimeInMin))


    def getSimVolume(self, startTimeInMin, endTimeInMin):
        """GEt the simulated volume for the specified time
        period """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        result = 0
        for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                             self.simTimeStepInMin)):
            result += self._simVolume[stTime, enTime]

        return result 

    def getSimFlow(self, startTimeInMin, endTimeInMin):
        """Get the simulated flow for the specified time period 
        in vph"""
        volume = self.getSimVolume(startTimeInMin, endTimeInMin)
        return  60.0 / (endTimeInMin - startTimeInMin) * volume

    def getSimTTInMin(self, startTimeInMin, endTimeInMin):
        """Return the mean travel time in minutes 
        of all the vehicles that entered the link in the
        specified time window
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        totalFlow = 0
        totalTime = 0
        
        if (startTimeInMin, endTimeInMin) in self._simMeanTT:
            return self._simMeanTT[startTimeInMin, endTimeInMin]

        for (stTime, enTime), flow in self._simVolume.iteritems():
            if stTime >= startTimeInMin and enTime <= endTimeInMin:
                binTT = self._simMeanTT[(stTime, enTime)]

                if binTT > 0 and flow > 0:
                    totalFlow += flow
                    totalTime += self._simMeanTT[(stTime, enTime)] * flow
                elif binTT == 0 and flow == 0:
                    continue
                else:
                    raise SimError("Movement %s has flow:%f and TT:%f "
                                           "for time period from %d to %d"  % 
                                           (self.iid, flow, binTT, 
                                            startTimeInMin, endTimeInMin))

        if totalFlow > 0:
            return totalTime / float(totalFlow) + self._penalty
        else:
            return (self.inEdge.getLengthInMiles() / 
                float(self.inEdge.getFreeFlowSpeedInMPH()) * 60 + self._penalty)

    def getSimSpeedInMPH(self, startTimeInMin, endTimeInMin):
        """Return the travel time on the first edge of the movement in 
        miles per hour"""

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        ttInMin = self.getSimTTInMin(startTimeInMin, endTimeInMin)
        lengthInMiles = self.inEdge.getLengthInMiles()
        return lengthInMiles / (ttInMin / 60.)

    def getFreeFlowSpeedInMPH(self):

        return self.upEdge.getFreeFlowSpeedInMPH()

    def getFreeFlowTTInMin(self):

        return self.upEdge.getFreeFlowTTInMin()
        
    def getObsCount(self, startTimeInMin, endTimeInMin):
        """Return the observed number of vehicles executing the
        movement in the input time span
        Attention!
        If there are Zero vehicles the function returns None
        """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        try:
            return self._obsCount[startTimeInMin, endTimeInMin]            
        except KeyError:
            result = 0 
            simTimeStep = self.simTimeStepInMin
            if not simTimeStep:
                raise SimError("To compute the count you need to set "
                                    "simulation time step")

            for i in range((endTimeInMin - startTimeInMin) / simTimeStep):
                multipleOfSimTimeStep = (i + 1) * simTimeStep
                result = 0

                for startTime, endTime in pairwise(range(startTimeInMin,
                                                     endTimeInMin + 1, multipleOfSimTimeStep)):
                    try:
                        result += self._obsCount[startTime, endTime]
                    except KeyError, e:
                        result = 0
                        break
                else:
                    return result
                    
            return result if result > 0 else None

    def hasCountInfo(self):
        """Return True if the movement contains count information else false"""
        return True if len(self._obsCount) else False

    def hasObsCount(self, startTimeInMin, endTimeInMin):
        """Return True if there is a count for the input time period  
        """
        return True if self.getObsCount(startTimeInMin, endTimeInMin) else False


    def iterCountPeriods(self, timeStepInMin=None):
        """Return the periods as tuples of start end endTime (in min)
        for which there is a count"""
        if not timeStepInMin:
            for start, end in sorted(self._obsCount.keys()):
                yield (start, end)
        else:
            minTime = min(self._obsCount.keys())[0]
            maxTime = max(self._obsCount.keys())[1]
            for start, end in pairwise(range(minTime, maxTime + 1, timeStepInMin)):
                yield (start, end)

    def iterCounts(self):
        """Return an iterator to the movement counts. Returned values 
        have the form (start, end), count"""
        for period in self.iterCountPeriods():
            yield period, self._obsCount[period]

    def setObsCount(self, startTimeInMin, endTimeInMin, count):
        """Specify the number of vehicles executing the movement 
        in the specified time window
        """

        self._validateInputTimes(startTimeInMin,endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if startTimeInMin >= endTimeInMin:
            raise SimError("Invalid time bin (%d %s). The end time cannot be equal or less "
                                "than the end time" % (startTimeInMin, endTimeInMin))
        if count < 0:
            raise SimError('Count for time period from %d to %d cannot be '
                                   'negative' % (startTimeInMin, endTimeInMin))
        self._obsCount[startTimeInMin, endTimeInMin] = count

    def setSimVolume(self, startTimeInMin, endTimeInMin, flow):
        """Specify the simulated number of vehicles that entered the edge
        in the specified time window"""
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        self._simVolume[startTimeInMin, endTimeInMin] = flow

    def setSimTTInMin(self, startTimeInMin, endTimeInMin, averageTTInMin):
        """Enter the simulated average travel time for the 
        specified time window"""

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        if averageTTInMin < 0:
            raise SimError("The travel time on movement cannot be negative" %
                                   self.iid)
        if averageTTInMin == 0:
            if self.getSimFlow(startTimeInMin, endTimeInMin) > 0:
                raise SimError("The travel time on movement %s with flow %d from %d to %d "
                                       "cannot be 0" % (self.iid, 
                                                        self.getSimFlow(startTimeInMin, endTimeInMin),
                                                        startTimeInMin, endTimeInMin))
            else:
                return

        #TODO: fix this. The problem is that the user defined edge length is different than the computed one.
        #As a result the free flow tt is not accurate
#        if averageTTInMin < self.getFreeFlowTTInMin():
#            raise SimError("Movement %s cannot have a travel time %f that is less"
#                                   " than its free flow travel time %f" %
#                                   (self.iid, averageTTInMin, self.getFreeFlowTTInMin()))

        if self.getSimFlow(startTimeInMin, endTimeInMin) == 0:
            raise SimError('Cannot set the travel time on a movement with zero flow')

        self._simMeanTT[startTimeInMin, endTimeInMin] = averageTTInMin
        
    def getTimeVaryingCostAt(self, timeInMin):
        """Return the cost (in min) for the time period begining at the 
        input time"""
        period = int((timeInMin - self.simStartTimeInMin) // self._timeStep)
        return self._timeVaryingCosts[period]

    def getTimeVaryingCostTimeStep(self):
        """Return the time step that is used for the time varying costs"""
        return self._timeStep
    
    def setTimeVaryingCosts(self, timeVaryingCosts, timeStep):
        """Inputs:timeVaryingCosts is an array containing the cost 
        of the edge in each time period. timeStep is the interval 
        length in minutes"""
        #make sure the costs are positive. 
        self._timeStep = timeStep
        for cost in timeVaryingCosts:
            assert cost > 0
        self._timeVaryingCosts = timeVaryingCosts
    
        
        

