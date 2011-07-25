__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import weakref 

from errors import PhaseError

class Phase(object):
    """Represents a Vista Phase"""

    def __init__(self, timePlan, phaseNumber, green, amber):
        """
        The constructor for Vista phase objects takes the following inputs:
        
        **Parameters**

        timePlan: a Vista TimePlan object in which the phase belongs
        phaseNumber: int
        amber: int
        green: int
        
        **Raises**
        PhaseException

        **Examples**

        """
        
        self._timePlan = timePlan
        #TODO why would I need such a thing? The timeplan should provide such info
        self._node = weakref.proxy(timePlan.getNode())

        self._phaseNumber = phaseNumber
        self.green = green
        self.amber = amber

        #TODO. If a movement gets deleted you have a problem here
        #vista does not have movements so I have a list that has the movement.iids
        self._movements = [] # weakref.WeakValueDictionary()

    def addMovement(self, *args):
        """Add the movement with the provided iid to the list of movements being served by the phase

        **Parameters**
        A three item tuple representing the movement iid of a movement e.g. (u"1", u"20", u"32")
        or: the three node ids representing the movement e.g. addMovment("1", "20", "32")

        **Raises**

        PhaseException 

        **Examples**

        """
        if len(args) == 1:
            movementIid = args[0]
        elif len(args) == 3:
            movementIid = tuple(args)
        else:
            #TODO I do not like this error message
            raise TypeError("Add movement not invoked properly. Please look at the docstring")

        #TODO: you should delegate this inforation to the timeplan and not the node
        #Vista does not have movements! So nothing for me to do 
        #if not self._node.hasMovement(movementIid):
        #    raise PhaseError("The movement %s does not exist" % str(movementIid))
        
        if self.hasMovement(movementIid):
            raise PhaseError("The movement %s already exists" % str(movementIid))

        #movement = self._node.getMovement(movementIid)
        movement = self._timePlan.getNode().getMovement(movementIid)
        self._movements.append(movement)

    def __repr__(self):
        """Return a string representation of the phase"""
        
        if self.getNumMovements() == 0:
            raise PhaseError("The number of movements in the phase is zero")

        nodeId = self._node.id
        if self._phaseNumber < 9 and self._phaseNumber > 0:
            phaseId = "0%d" % self._phaseNumber
        elif phaseNumber > 9 and self._phaseNumber < 100:
            phaseId = "%d" % self._phaseNumber
        else:
            raise PhaseError("Phase number %d is not valid" % self._phaseNumber)

        header = "%s%s\t1\t%s\t0\t%d\t0\t%d\t%d\t%d" % (nodeId, phaseId, nodeId, self._phaseNumber, 
                                                  self.amber, self.green, self.getNumMovements())

#        fromNodeIds = ",".join([mov.nodeAid for mov in self.iterMovements()])
#        toNodeIds = ",".join([mov.nodeCid for mov in self.iterMovements()])

        fromLinkIds = ",".join([mov.upLink.id for mov in self.iterMovements()])
        toLinkIds = ",".join([mov.downLink.id for mov in self.iterMovements()])
        
        return "%s\t{%s}\t{%s}" % (header, fromLinkIds, toLinkIds)

    def __str__(self):
        return self.__repr__()

    def hasMovement(self, movementIid):
        """Return True if a movement with the given iid belongs to the phase else False"""
        return True if movementIid in [mov.iid for mov in self.iterMovements()] else False
        
    def iterMovements(self):
        """Return an iterator to the movements assigned to the phase"""
        return iter(self._movements)

    def getNumMovements(self):
        """Return the number of movements assigned to the phase"""
        return len(self._movements)
