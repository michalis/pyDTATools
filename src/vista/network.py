__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import logging
from itertools import chain, ifilter, imap
from operator import itemgetter, attrgetter
import os

from vista.node import Node
from vista.link import Link
from vista.movement import Movement
from vista.timeplan import TimePlan
from vista.zone import Zone
from vista.demand import Demand 
from netUtils.utils import isShapeNode, doLineStringsCross, iterRegularNodes, iterRegularLinks
from shapefile.shpWriter import ShpWriter
from geometry.featureCollection import FeatureCollection 
from utils.odict import OrderedDict
from vista.errors import VistaError, NodeError, LinkError, MovementError, \
    PhaseError, TimePlanError, ZoneError    

class Network(object):
    """Holds all the elements of a vista network
    nodes, links, zone connectors, signals"""

    CENTROID_AUTO_ID_ADD = 100000
    CONNECTOR_AUTO_ID_ADD = 100000


    NODES_FILE = "nodes.txt"
    LINKS_FILE = "links.txt"
    LINK_DETAILS_FILE = 'linkdetails.txt'
    LINK_BAYS_FILE = 'linkbays.txt'
    CONTROLS_FILE = 'controls.txt'
    SIGNAL_FILE = 'signals.txt'
    PHASE_FILE = 'phase.txt'

    DEMAND_FILE = 'demand.txt'
    DEMAND_PROFILE_FILE = 'demandProfile.txt'

    @classmethod
    def read(cls, projectFolder):
        """Read a vista network from the text files in the 
        project folder and return it"""
        

        net = Network()
        net.projectFolder = projectFolder

        for node in Node.readFromFile(net):
            net.addNode(node)

        for link in Link.readFromFile(net):
            net.addLink(link)
        
        # the controls
        # the signals 
        #the phases 
        #denand 
        #link bays 
        return net

    def __init__(self):

        self.projectFolder = None
        self._nodes = OrderedDict()
#        self._intersectionByName = {}
        self._linksByIid = OrderedDict()
        self._linksById = OrderedDict()
        self._zones = OrderedDict()
        self._demand = None

        self._maxVertexId = 0
        self._maxNodeId = 0
        self._maxEdgeId = 0
        self._maxLinkId = 0

    def empty(self):
        """Discard all the elements associated with this network"""
        self._nodes = OrderedDict()
        self._linksByIid = OrderedDict()
        self._linksById = OrderedDict()

    def addRegularNode(self, id, x, y):
        """Add a node  with the specified 
        attributes to the network and return a reference to it"""
        INode = Node(self, id, Node.TYPE_REGULAR, x, y)
        self.addNode(INode)
        return INode

    def addCentroid(self, id, x, y):
        """Add a centroid with the specified attributes to the 
        network and return a reference to it"""
        INode = Node(self, id, Node.TYPE_CENTROID, x, y)
        self.addNode(INode)
        return INode
            
    def addNode(self, INode):
        """Add the input node(regular node or centroid) to the network"""
        if INode.id in self._nodes:
            raise NodeError("Duplicate Node Id %s" % INode.id)

        if int(INode.id) > self._maxVertexId:
            self._maxVertexId = int(INode.id)
        if int(INode.id) > self._maxNodeId and isinstance(INode, Node):
            self._maxNodeId = int(INode.id)

        self._nodes[INode.id] = INode

    def deleteNode(self, nodeId):
        """Delete the node with the given id an all the associated links"""
        #TODO you have to update the self._maxVertexId and the rest
        nodeToDelete = self.getNode(nodeId)
        linksToDelete = [link for link in chain(nodeToDelete.iterIncidentLinks(), 
                                                nodeToDelete.iterEmanatingLinks())]

        for link in linksToDelete:
            self.deleteLink(link.nodeA.id, link.nodeB.id)

#        for iLink in nodeToDelete.iterIncidentLinks():
#            self.deleteLink(iLink.nodeAid, iLink.nodeBid)
#        for eLink in nodeToDelete.iterEmanatingLinks():
#            self.deleteLink(eLink.nodeAid, eLink.nodeBid)
            
        del self._nodes[nodeId]
            
    def addRegularLink(self, id_, nodeA, nodeB, lengthInFeet, 
                       speedInMilesPerMinute, saturationFlowPCPHGPL, numMidBlockLanes):
        """Add a regular link with the provided attributes to the network"""

        if nodeA.isCentroid():
            #TODO I do not like this error message
            raise LinkError("A regular link cannot be connected to a centroid")
        if nodeB.isCentroid():
            raise LinkError("A regular link cannot be connected to a centroid")

        ILink = Link(self, id_, Link.TYPE_REGULAR, nodeA, nodeB,
                 speedInMilesPerMinute, saturationFlowPCPHGPL, numMidBlockLanes)

        self.addLink(ILink)
        return ILink

    def addConnector(self, id_, nodeA, nodeB, 
                       speedInMilesPerMinute, saturationFlowPCPHGPL, numMidBlockLanes):
        """Add a centroid connnector link with the provided attributes to the network"""
        
        #TODO the error messages do not provide adequate information
        if nodeA.isCentroid() and nodeB.isCentroid():
            raise LinkError("A connector cannot be connected to two centroids")
        if nodeA.isRegular() and nodeB.isRegular():
            raise LinkError("A connector cannot be connected to two regular nodes")

        ILink = Link(self, id_, Link.TYPE_CENTROID_CONNECTOR, nodeA, nodeB, 
                 speedInMilesPerMinute, saturationFlowPCPHGPL, numMidBlockLanes)

        self.addLink(ILink)
        return ILink

    def addLink(self, ILink):
        """Add the input link(regular or centroid connector) to the network"""
        if ILink.iid in self._linksByIid:
            raise LinkError("Duplicate Link iid %s" % str(ILink.iid))
        if ILink.id in self._linksById:
            raise LinkError("Duplicate Link id %s" % str(ILink.id))
        
#        if ILink.id in [link.id for link in self.iterLinks()]:
#            raise LinkException("A link with the same id %s already exists" %
#                                ILink.id)

        #TODO do I need this? 
        if self.hasLink(ILink.nodeAid, ILink.nodeBid):
            raise LinkError("A Link startting from %s to %s already exists" %
                                (ILink.nodeAid, ILink.nodeBid))

        self._linksByIid[ILink.iid] = ILink
        self._linksById[ILink.id] = ILink

        ILink.nodeB.addIncidentLink(ILink)
        ILink.nodeA.addEmanatingLink(ILink)

        if int(ILink.id) > self._maxEdgeId:
            self._maxEdgeId = int(ILink.id)
        if int(ILink.id) > self._maxLinkId and isinstance(ILink, Link):
            self._maxLinkId = int(ILink.id)

        #add all the movements to the the link
        for incidentLink in ILink.nodeA.iterIncidentLinks():
            incidentLink.addEmanatingMovement(ILink, Movement.TURN_OTHER1)
            #ILink.addIncidentMovement(incidentLink, Movement.TURN_OTHER1)
        for emanatingLink in ILink.nodeB.iterEmanatingLinks():
            ILink.addEmanatingMovement(emanatingLink, Movement.TURN_OTHER1)
            #emanatingLink.addIncidentMovement(ILink, Movement.TURN_OTHER1)

    def deleteLink(self, nodeAid, nodeBid):
        """Delete the link with the provided iid or the one 
        starting from nodeAid and ending to nodeBid"""
#        if len(args) == 1:
#            linkIid = args[0]
#        elif len(args) == 2:
#            linkIid = tuple(args)
#        else:
#            TypeError("Incorrect invocation of deleteLink")
        
        if not self.hasLink(nodeAid, nodeBid):
            raise LinkError("Cannnot delete link %s because it does not exist" % str(nodeAid, nodeBid))

        linkToDelete = self.getLink(nodeAid, nodeBid)

        nodeA = linkToDelete.nodeA 
        nodeB = linkToDelete.nodeB

#        nodeA.deleteSuccessorNode(nodeB)
#        nodeA.deleteEmanatingLink(linkToDelete)
#        nodeB.deletePredecessorNode(nodeA)
        nodeB.deleteLink(linkToDelete)
        
        del self._linksByIid[linkToDelete.iid]
        del self._linksById[linkToDelete.id]
        
        if nodeA.hasTimePlan():
            nodeA.deleteTimePlan()
            print "deleted the timeplan of node: %s" % nodeAid
        if nodeB.hasTimePlan():
            nodeB.deleteTimePlan()
            print "deleted the timeplan of node: %s" % nodeBid

    def addTimePlan(self, nodeId, offset):
        """Add a timeplan with the given offset to the node with the specified id"""
        node = self.getNode(nodeId)
        node.addTimePlan(offset)
        return timePlan

    def deleteTimePlan(self, nodeId):
        """Delete the timeplan with the given id"""
        node = self.getNode(nodeId)
        node.deleteTimePlan()
    
    def iterNodes(self):
        """Reuturn an iterator to the Nodes"""
        return iter(self._nodes.values())

    def iterRegularNodes(self):
        """Return an iterator to all the regular nodes in the network
        (not centroid connectors)"""
        return ifilter(lambda link: link.isRegular(), self.iterNodes())

    def iterCentroids(self):
        """Return an iterator to all the centroids in the network"""
        return ifilter(lambda node: node.isCentroid(), self.iterNodes())

    def iterTimePlans(self):
        """Return an iterator to the timeplans in the network"""
        return imap(lambda node: node.getTimePlan(),
                    ifilter(lambda node: node.hasTimePlan(), self.iterNodes()))

    def iterLinks(self):
        """Return an iterator to the Links"""
        return iter(self._linksByIid.values())
    
    def iterRegularLinks(self):
        """Return an iterator to all the regular links"""
        return ifilter(lambda link: link.isRegular(), self.iterLinks())

    def iterCentroidConnectors(self):
        """Return an iterator to all the centroid connectors"""
        return ifilter(lambda link: link.isCentroidConnector(), self.iterLinks())

    def iterZones(self):
        
        return self._zones.itervalues()

    def copy(self):
        """Return a copy of the network"""
        raise Exception("Not implemeted yet")

    def getDemand(self):

        self._demand = Demand(self)
        return self._demand

    def getZone(self, zoneId):
        """Return the zone with the specified id"""
        try:
            return self._zones[zoneId]
        except KeyError:
            raise ZoneError("Zone %s does not exist in the network" %
                                str(zoneId))

    def getNode(self, nodeId):
        """Return the node in the network with the given id if it
        exists otherwise raise NodeException"""
        try:
            return self._nodes[nodeId]
        except KeyError:
            raise NodeError("Node %s does not exist in the network" %
                                str(nodeId))

    def getLink(self, *args):
        """Return the link starting from the node with id
        nodeAid and ending to the node with nodeBid"""

        if len(args) == 2:
            nodeAid = args[0]
            nodeBid = args[1]
            try:
                return self._linksByIid[(nodeAid, nodeBid)]
            except KeyError, e:
                raise LinkError("Link from %s to %s does not exist" % (nodeAid, nodeBid))
        elif len(args) == 1:
            try:
                if isinstance(args[0], str):
                    return self._linksById[args[0]]
                elif isinstance(args[0], tuple):
                    return self._linksByIid[args[0]]                
            except KeyError, e:
                if isinstance(args[0], str):
                    raise LinkError("Link with iid %s does not exist" % args[0])
                else:
                    raise LinkError("Link with iid %s does not exist" % args[0])
        else:
            raise TypeError("Incorrect invocation of getLink")

    def hasNode(self, nodeId):
        """Return True if the network has a node with 
        the supplied id otherwise False"""
        return True if nodeId in self._nodes else False

    def hasLink(self, nodeAid, nodeBid):
        """Return True if the there is a link between nodes A
        and B with ids nodeAid and nodeBid"""
#        if len(*args) == 1:
#            linkIid = args[0]
#        elif len(*args) == 2:
#            linkIid = tuple(*args)
#        else:
#            raise TypeError("HasLink takes as an argument either the linkIid or "
#                            "nodeAid and nodeBid")
        return True if (nodeAid, nodeBid) in self._linksByIid else False

    def getNumVertices(self):
        """Return the number of nodes"""
        return len(self._nodes)

    def getNumNodes(self):
        """Return the number of regular nodes (not connectors) in the network"""
        return sum(imap(lambda node: 1, self.iterRegularNodes()))

    def getNumCentroids(self):
        """Return the number of centroids in the network"""
        return sum(imap(lambda conn: 1, self.iterCentroids()))

    def getNumTimePlans(self):
        """Return the number of time plans"""
        return sum([node.hasTimePlan() for node in self.iterNodes()])

    def getNumEdges(self):
        """Return the number of edges (links + connectors)"""
        return len(self._linksByIid) 

    def getNumLinks(self):
        """Return the number of regular links (not centroid connectors)"""
        return sum(imap(lambda link: 1, self.iterRegularLinks()))

    def getNumConnectors(self):
        """Return the number of centroid connectors in the network"""
        return sum(imap(lambda conn: 1, self.iterCentroidConnectors()))
    
    def getNodeCardinality(self, nodeId):
        """Return a tuple containing the number of 
        emanating links followed by the number of 
        incident links"""
        return self.getNode(nodeId).getNodeCardinality()

    def addZone(self, id, loadingCentroid, unLoadingCentroid):
        """Add a zone to the the network with the given id and the 
        two centroid nodes used for loading and unloading vehicles"""
        if not self.hasNode(loadingCentroid.id) or not loadingCentroid.isCentroid():
            raise ZoneError("A centroid with %s does not exist in "
                                "the network" % loadingCentroid.id)
        if not self.hasNode(unLoadingCentroid.id) or not unLoadingCentroid.isCentroid():
            raise ZoneError("A centroid with %s does not exist in "
                                "the network" % loadingCentroid.id)
        if id in self._zones:
            raise ZoneError("A zone with id %d already exists" % id)

        self._zones[id] = Zone(self, id, loadingCentroid, unLoadingCentroid)

    def deleteZone(self, id):
        raise Exception("Not implemented yet")

    def write(self, projectFolder):
        """Writes all the network elemments to the folloing files:
        controls.txt
        signals.txt
        phases.txt
        linkBays.txt
        links.txt
        linkdetails.txt
        nodes.txt
        """
        #TODO fix this...
        fileName = "nodes.txt"
        try:
            self.writeNodeInfo(projectFolder)
            self.writeLinkInfo(projectFolder)
            self.writeSignalInfo(projectFolder)
        except IOError:
            raise VistaError("Failed to write the network info in the project folder %s" %
                             projectFolder)
    
    def writeNodeInfo(self, projectFolder):
        """Write the node info to nodes.txt"""
        output = open(os.path.join(projectFolder, "nodes.txt"), "w")
        for node in self.iterNodes():
            output.write("%s\n" % str(node))
        output.close()
                      
    def writeLinkInfo(self, projectFolder):
        """Write the all the link related info in the following files
        links.txt, link.details.txt, linkbays.txt"""
        outputLink = open(os.path.join(projectFolder, "links.txt"), "w")
        outputLinkDetails = open(os.path.join(projectFolder, "linkdetails.txt"), "w")
        outputLinkBays = open(os.path.join(projectFolder, "linkbays.txt"), "w")                      
        for link in self.iterLinks():
            outputLink.write("%s\n" % str(link))
            outputLinkDetails.write("%s\n" % link.getLinkDetailsAsString())
            outputLinkBays.write("%s\n" % link.getLinkBaysAsString())
        outputLink.close()
        outputLinkDetails.close()
        outputLinkBays.close()

    def writeSignalInfo(self, projectFolder):
        """Write all the signal related info in the following files:
        signals.txt, controls.txt, phase.txt"""
        outputPhase = open(os.path.join(projectFolder, "phase.txt"), "w")
        outputControl = open(os.path.join(projectFolder, "controls.txt"), "w")
        outputSignals = open(os.path.join(projectFolder, "signals.txt"), "w")
        for timePlan in self.iterTimePlans():
            outputControl.write("%s\n" % timePlan.getControlString())
            outputPhase.write("%s" % timePlan.getPhasesAsString())
            outputSignals.write("%s\n" % timePlan.getSignalString())                                
        outputPhase.close()
        outputControl.close()
        outputSignals.close()
        
    def exportNodesToShp(self, fileName=None):
        """Export the network nodes to a shapefile"""
        if not fileName:
            fileName = os.path.join(self.projectFolder, "nodes.shp")

        fCollection = FeatureCollection()
        for node in self.iterNodes():
            fCollection.addFeature(node)
        fCollection.determineHeader()
        shpWriter = ShpWriter(fileName)
        shpWriter.writeFeatures(fCollection)
    
    def exportLinksToShp(self, fileName=None):
        """Export the network links to a shapefile"""
        if not fileName:
            fileName = os.path.join(self.projectFolder,"links.shp")

        fCollection = FeatureCollection()
        for link in self.iterLinks():
            fCollection.addFeature(link)
        fCollection.determineHeader()            
        shpWriter = ShpWriter(fileName)
        shpWriter.writeFeatures(fCollection)

    def getNewRegularNodeId(self):
        """Return a new regular node id that is one plus the highest node id"""
        newId = str(self._maxNodeId + 1)
        if newId in self._nodes:
            return str(self._maxVertexId + 1)
        else:
            return newId

    def getNewRegularLinkId(self):
        """Return a new regular link id that is one plus the highest link id"""
        newId = str(self._maxLinkId + 1)
        if newId in self._linksById:
            return str(self._maxEdgeId + 1)
        else:
            return  newId

    def getNewCentroidId(self):
        """Return a new id that is one plus the higest vertex id. If there 
        are no centroid ids add Network.CENTROID_AUTO_ID_ADD to the max 
        vertex Id and return it"""
        if self.getNumCentroids() == 0:
            return str(self._maxVertexId + Network.CENTROID_AUTO_ID_ADD)
        else:
            return str(self._maxVertexId + 1)

    def getNewConnectorId(self):
        """Return a new id that is one plus the highest edgeId. If there 
        are no connectors in the network add Network.CONNECTOR_AUTO_ID_ADD
        to the max edgeid and return it.""" 
        if self.getNumConnectors() == 0:
            return str(self._maxEdgeId + Network.CONNECTOR_AUTO_ID_ADD)
        else:
            return str(self._maxEdgeId + 1)

def splitLink(net, linkToSplit):
    """Split the link defined by upNode and downNode into two 
    links of equal size and delete the old link connecting the 
    upNode to downNode. if the old link has a mate link
    split that one too. Return the middle node.

    if there is a mate of link split that too

    if the link has a bay you have take that into account

    """
    if isinstance(linkToSplit, tuple):
        linkToSplit = net.getLink(link)

    upNode = linkToSplit.nodeA
    downNode = linkToSplit.nodeB

    if linkToSplit.getNumBays() > 0:
        raise NetworkError("I cannot split a link containing bays")

    midX = (upNode.x + downNode.x) / 2
    midY = (upNode.y + downNode.y) / 2
    #TODO
    newNodeId = net.getNewRegularNodeId()
    middleNode = net.addRegularNode(newNodeId, midX, midY)

    def addTwoNewLinks(linkToSplit, middleNode):
        #newLink1 = Link.create(parameters)
        #net.addLink(newLink1)

        if not linkToSplit.isCentroidConnector():
            net.addRegularLink(net.getNewRegularLinkId(), linkToSplit.nodeA, middleNode,
                               linkToSplit.lengthInFeet / 2, linkToSplit.speedInMilesPerMinute,
                               linkToSplit.satFlowPCPHGPL, linkToSplit.numMidBlockLanes)            

            net.addRegularLink(net.getNewRegularLinkId(), middleNode, linkToSplit.nodeB,
                               linkToSplit.lengthInFeet / 2, linkToSplit.speedInMilesPerMinute,
                               linkToSplit.satFlowPCPHGPL, linkToSplit.numMidBlockLanes)
        else:
            if linkToSplit.nodeB.isCentroid():
                net.addRegularLink(net.getNewRegularLinkId(), linkToSplit.nodeA, middleNode,
                               linkToSplit.lengthInFeet / 2, linkToSplit.speedInMilesPerMinute,
                               linkToSplit.satFlowPCPHGPL, linkToSplit.numMidBlockLanes)            
                net.addConnector(net.getNewConnectorId(), middleNode, linkToSplit.nodeB, 
                                 linkToSplit.speedInMilesPerMinute,
                                 linkToSplit.satFlowPCPHGPL, linkToSplit.numMidBlockLanes)                               
            else:
                net.addConnector(net.getNewConnectorId(), linkToSplit.nodeA, middleNode,
                                linkToSplit.speedInMilesPerMinute,
                               linkToSplit.satFlowPCPHGPL, linkToSplit.numMidBlockLanes)            
                net.addRegularLink(net.getNewRegularLinkId(), middleNode, linkToSplit.nodeB, 
                                 linkToSplit.lengthInFeet / 2, linkToSplit.speedInMilesPerMinute,
                                 linkToSplit.satFlowPCPHGPL, linkToSplit.numMidBlockLanes)                               
                
    if linkToSplit.hasMate():
        mateToSplit = linkToSplit.getMate()
        addTwoNewLinks(mateToSplit, middleNode)
        net.deleteLink(mateToSplit.nodeAid, mateToSplit.nodeBid)

    addTwoNewLinks(linkToSplit, middleNode)
    net.deleteLink(linkToSplit.nodeAid, linkToSplit.nodeBid)
    return middleNode

def removeCentroidConnectorsFromIntersections(net, connectorFactory):

    linkIds = [link.iid for link in net.iterLinks()]
    
    for linkId in linkIds:
        if not net.hasLink(linkId):
            continue
        
        link = net.getLink(linkId)

        if link.isCentroidConnector():

            print "I am examining ", link.iid
            connector = link

            if connector.nodeA.isRegular():
                towardsCentroid = True
                centroid = connector.nodeB
                intersection = connector.nodeA
            elif connector.nodeB.isRegular():
                towardsCentroid = False
                centroid = connector.nodeA
                intersection = connector.nodeB
            else:
                raise LinkError("Link %s connects two centoids" % connector.iid)

            accNodes = list(iterRegularNodes(intersection.iterAssociatedNodes()))
            #if the zone connector not conected to an intersection continue
            if len(accNodes) < 3:
                continue

            newConnector = None

            if towardsCentroid:
                iterLinks = iterRegularLinks(intersection.iterIncidentLinks())
            else:
                iterLinks = iterEmanatingLinks(intersection.iterIncidentLinks())

            iterLinks = sorted(iterLinks, key = lambda l:l.length, reverse=True)

            shapeNode = None
            for iLink in iterLinks:
                if isShapeNode(iLink.mateOfNode(intersection.iid)):
                    shapeNode = iLink.mateOfNode(intersection.iid)
                    lineString = LineString([shapeNode, centroid])
                    if not doLineStringsCross(lineString, iterLinks):
                        if towardsCentroid: 
                            if net.hasLink(shapeNode.iid, centroid.iid):
                                continue
                            newConnector = connectorFactory(net, shapeNode, centroid)
                        else: 
                            if net.hasLink(centroid.iid, shapeNode.iid):
                                continue
                            newConnector = connectorFactory(net, centroid, shapeNode)

            if newConnector:
                net.deleteLink(connector.iid)
                net.addLink(newConnector)
                newConnector = None
                continue

            #a shapenode was not found. Find the lengthiest link closeby 
            #split it and attache the zone connector
            
            for iLink in iterLinks:
                midPoint = Point((iLink.nodeA.x + iLink.nodeB.x) / 2,
                                 (iLink.nodeA.y + iLink.nodeB.y) / 2)
                lineString = LineString([iLink.mateOfNode(intersection.iid), centroid])
                if not doLineStringsCross(lineString, iterLinks):
                    #split the iLink
                    newNodeId = net.genNewNodeId()
                    middleNode = net.splitLink(iLink, newNodeId)
                    
                    if towardsCentroid:
                        newConnector = connectorFactory(net, middleNode, centroid)
                    else:
                        newConnector = connectorFactory(net, centroid, middleNode)
                    net.addLink(newConnector)
                    net.deleteLink(connector.iid)
                    
                    break
            else:
                logging.error("Unable to remove the zone connector %s", str(connector.iid))
#                raise Exception("Unable to connect the zone connector")

