__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import logging

from pbCore.vista.phase import Phase
from errors import TimePlanError

class TimePlan(object):

    """Represents a Vista TimePlan"""
    
    CONTROL_TYPE_PRETIMED = "448"
    
    def __init__(self, node, offset):
        """Constructor for the Vista TimePlan objects takes the following arguments

        **Parameters**
        
        node: a Vista Node object for which the timePlan applies
        offset: int
    
        **Raises**
        TimePlanException

        **Examples**

        """

        self._node = node
        self.offset = offset
        self.cycleLength = 0

        self._phases = []  # phaseNumbers are incrimental starting from zero 

    def getNodeId(self):
        """Return the node id of the node the timeplan applies"""
        return self._node.id
    
    def addPhase(self, *args):
        """Add the provided phase to end of the existing ones"""
        #TODO: should you check the phaseNumber?
        if len(args) == 1:
            phase = args[0]
            self._phases.append(phase)
            self.cycleLength += phase.green
            self.cycleLength += phase.amber
        elif len(args) == 2:
            green = args[0]
            amber = args[1]
            phase = Phase(self, len(self._phases) + 1, green, amber)
            self._phases.append(phase)
            self.cycleLength += phase.green
            self.cycleLength += phase.amber            
        else:
            #TODO fix this error message
            raise TypeError("Incorrct invocation of addPhase")
        
        return phase

    def iterPhases(self):
        """Return an iterator to the phases"""
        return iter(self._phases)

    def iterMovements(self):
        """Return an iterator to all the movements that in the plan serves. The same 
        movement may appear twice if it belongs to more than one phase"""
        return iter([mov for phase in self.iterPhases() for mov in phase.iterMovements()])

    def hasMovement(self, movementIid):
        """Return True if the timeplan has the movement False otherwise"""
        for movement in self.iterMovements():
            if movementIid == movement.iid:
                return True
        return False

    def getControlString(self):
        
        return "%s\t%s" % (self.getNode().id, TimePlan.CONTROL_TYPE_PRETIMED)

    def getPhasesAsString(self):
        """Return a multiline string each line representing a phase"""
        result = ""
        for phase in self.iterPhases():
            result += "%s\n" % str(phase)
        return result

    def getSignalString(self):
        
        return "%s\t%s\t%d" % (self.getNode().id, TimePlan.CONTROL_TYPE_PRETIMED, self.offset)

    def getNumPhases(self):
        """Return the number of phases"""
        return len(self._phases)

    def getNode(self):
        """Return the node the timeplan refers to"""
        return self._node

    def validate(self):
        """Validate all the elements of the TimePlan

        **Raises**
        TimePlanException

        """
        #check that the plan has more than one phase
        if self.getNumPhases() < 2:
            raise TimePlanError("The number of phases cannot be less than 2")

        #chekc that each phase has at least one movement 
        for phase in self.iterPhases():
            if phase.getNumMovements() < 1:
                raise TimePlanError("The number of movements in a phase "
                                    "cannot be less than one")

        #check that each phase has min or max green greater than zero
        for phase in self.iterPhases():
            if phase.green <= 0:
                raise TimePlanError("The min Green should be a positive number")
    
        if self.cycleLength <= 0:
            raise TimePlanError("The cycle length should be greater than zero")

        #check that the sum of the times is equal to the cycle time
        cycleLength = sum([phase.green + phase.amber for phase in self.iterPhases()])
        if cycleLength != self.cycleLength:
            raise TimePlanError("The sum of the green times for the pretimed signal "
                                    "is not the same with the cycle length")
        
        #check that none of the movmeents is a UTurn movement
        for phase in self.iterPhases():
            for movement in self.iterMovements():
                if movement.isUTurn():
                    raise TimePlanError("Node %s. Movement %s is a UTurn and cannot belong to "
                                        "the time plan" % (self._node.id, movement.iid))

        #check if all the node movements are the same with the 
        #phase movements         
        phaseMovements = set([mov.iid for phase in self.iterPhases() for mov in phase.iterMovements()]) 
        nodeMovements = set([mov.iid for iLink in self._node.iterIncidentLinks() 
                               for mov in iLink.iterEmanatingMovements() if not mov.isUTurn()])
                             
        if phaseMovements != nodeMovements:

            nodeMovsNotInPhaseMovs = nodeMovements.difference(phaseMovements)
            phaseMovsNotInNodeMovs = phaseMovements.difference(nodeMovements)

            message = ("Node %s. The phase movements are not the same with node movements." 
                                "\n\tNode movements missing from the phase movements: \n\t\t%s" 
                                "\n\tPhase movements not registered as node movements: \n\t\t%s" % 
                                (self.getNode().iid, "\n\t\t".join(map(str, nodeMovsNotInPhaseMovs)),
                                 "\n\t\t".join(map(str, phaseMovsNotInNodeMovs))))

            logging.warning(message)
            #raise TimePlanException(message)
