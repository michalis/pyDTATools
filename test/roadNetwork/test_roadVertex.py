__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import nose.tools

from roadNetwork.vertex import Vertex
from roadNetwork.edge import Edge
from roadNetwork.errors import GraphError
from roadNetwork.test.simpleNetworks import constructIntersection, getSimpleNet

class TestVertex:

    def test_construction(self):
        
        v1 = Vertex("1", 1.0, 1.0)

        v1.getNumOutEdges() == 0
        v1.getNumInEdges() == 0

        v1.getCardinality() == (0, 0)

        v1.getNumMovements() == 0

    def test_getOutEdge(self):

        v4 = Vertex("4", 200, 100)
        v5 = Vertex("5", 100, 100) 

        e45 = Edge(v4, v5, 2)
        e54 = Edge(v5, v4, 3)
        
        v5.addOutEdge(e54)

        assert e54 == v5.getOutEdge('4')
        nose.tools.assert_raises(GraphError, v5.getOutEdge, "10")

        assert v5.hasOutEdge("4")
        assert not v5.hasOutEdge("11")

    def test_incidentEdge(self):
        
        v4 = Vertex("4", 200, 100)
        v5 = Vertex("5", 100, 100) 

        e45 = Edge(v4, v5, 2)
        e54 = Edge(v5, v4, 3)
        
        v5.addInEdge(e45)
        
        assert e45 == v5.getInEdge("4")
        nose.tools.assert_raises(GraphError, v5.getInEdge, "40")

        assert v5.hasInEdge("4")
        assert not v5.hasInEdge('100')

    def test_addOutEdge(self):

        v4 = Vertex("4", 200, 100)
        v5 = Vertex("5", 100, 100) 

        v45 = Edge(v4, v5, 2)
        v54 = Edge(v5, v4, 3)

        nose.tools.assert_raises(GraphError, v5.addOutEdge, v45)
        v5.addOutEdge(v54)
        assert v5.getNumOutEdges() == 1
        nose.tools.assert_raises(GraphError, v5.addOutEdge, v54)

    def test_addInEdge(self):

        v4 = Vertex("4", 200, 100)
        v5 = Vertex("5", 100, 100) 

        v45 = Edge(v4, v5, 2)
        v54 = Edge(v5, v4, 3)

        nose.tools.assert_raises(GraphError, v5.addInEdge, v54)
        v5.addInEdge(v45)
        assert v5.getNumInEdges() == 1
        nose.tools.assert_raises(GraphError, v5.addInEdge, v45)

    def test_constructIntersection(self):
        
        v5 = constructIntersection()

        assert v5.getNumOutEdges() == 4
        assert v5.getNumInEdges() == 4

    def test_iterOutEdges(self):

        v5 = constructIntersection()

        result = [edge.iid_ for edge in v5.iterOutEdges()]        
        answer = ['5 1', '5 2', '5 4', '5 3']
        assert result == answer

    def test_iterInEdges(self):
        
        v5 = constructIntersection()
        result = [edge.iid_ for edge in v5.iterInEdges()]
    
        answer = ['4 5', '2 5', '1 5', '3 5']
        assert result == answer 
        
    def test_getOutEdgeClockwise(self):
    
        v5 = constructIntersection()
        e54 = v5.getOutEdge("4")

        e53 = v5.getOutEdgeClockwise(e54)
        assert e53 == v5.getOutEdge("3")
        e51 = v5.getOutEdgeClockwise(e53)
        assert e51 == v5.getOutEdge("1")
        e52 = v5.getOutEdgeClockwise(e51)
        assert e52 == v5.getOutEdge("2")
        e54 = v5.getOutEdgeClockwise(e52)
        assert e54 == v5.getOutEdge("4")
        
    def test_getInEdgeCounterClockwise(self):
        
        v5 = constructIntersection()
        e35 = v5.getInEdge("3")

        e45 = v5.getInEdgeCounterClockwise(e35)
        assert e45 == v5.getInEdge("4")
        e25 = v5.getInEdgeCounterClockwise(e45)
        assert e25 == v5.getInEdge("2")
        e15 = v5.getInEdgeCounterClockwise(e25)
        assert e15 == v5.getInEdge("1")
        e35 = v5.getInEdgeCounterClockwise(e15)
        assert e35 == v5.getInEdge("3")
        
    def test_getInEdgeClockwise(self):

        v5 = constructIntersection()
        e35 = v5.getInEdge("3")
        
        e15 = v5.getInEdgeClockwise(e35)
        assert e15 == v5.getInEdge("1")
        
        e25 = v5.getInEdgeClockwise(e15)
        assert e25 == v5.getInEdge("2")
        
        e45 = v5.getInEdgeClockwise(e25)
        assert e45 == v5.getInEdge("4")
        
        e35 = v5.getInEdgeClockwise(e45)        
        assert e35 == v5.getInEdge("3")

    def test_getEdgeClockwise(self):

        net = getSimpleNet() 

        v5 = net.getVertex("5")
        
        edge15 = net.getEdge("1", "5")
        edge51 = net.getEdge("5", "1")
        edge25 = net.getEdge("2", "5")
        edge52 = net.getEdge("5", "2")
        edge45 = net.getEdge("4", "5")
        edge54 = net.getEdge("5", "4")
        edge35 = net.getEdge("3", "5")
        edge53 = net.getEdge("5", "3")

        result = v5.getEdgeClockwise(edge15)
        assert result == edge51
        result = v5.getEdgeClockwise(edge51)
        assert result == edge25
        result = v5.getEdgeClockwise(edge25)
        assert result == edge52
        result = v5.getEdgeClockwise(edge52)
        assert result == edge45
        result = v5.getEdgeClockwise(edge45)
        assert result == edge54
        result = v5.getEdgeClockwise(edge54)
        assert result == edge35
        result = v5.getEdgeClockwise(edge35)
        assert result == edge53
        result = v5.getEdgeClockwise(edge53)
        assert result == edge15 

        #for eEdge in v5.iterOutEdges():
        #    print eEdge, eEdge.midpoint, eEdge.midpoint2, eEdge._angle, v5.getOrientation(eEdge.midpoint2)

    def test_iterEdgesClockwise(self):

        net = getSimpleNet() 
        v5 = net.getVertex("5")

        result = [e.iid for e in v5.iterEdgesClockwise()] 
        answer = [('2', '5'), ('5', '2'), ('4', '5'), ('5', '4'), 
                  ('3', '5'), ('5', '3'), ('1', '5'), ('5', '1')]
        
        assert result == answer 
        
    def test_iterEdgePairs(self):

        net = getSimpleNet() 
        v5 = net.getVertex("5")

        result = [(e1.iid, e2.iid) for e1, e2 in v5.iterEdgePairs()] 

        answer = [(('2', '5'), ('5', '2')), (('5', '2'), ('4', '5')), 
                  (('4', '5'), ('5', '4')), (('5', '4'), ('3', '5')), 
                  (('3', '5'), ('5', '3')), (('5', '3'), ('1', '5')), 
                  (('1', '5'), ('5', '1')), (('5', '1'), ('2', '5'))]

        assert result == answer 

    def test_iterPredSuccAdjVertices(self):

        net = getSimpleNet()

        v1 = net.getVertex("1")

        assert v1.getNumPredecessorVertices() == 1
        assert v1.getNumSuccessorVertices() == 1
        assert v1.getNumAdjacentVertices() == 1

        v5 = net.getVertex("5")
        assert v5.getNumAdjacentVertices() == 4

    def test_adjacentVertices(self):

        net = getSimpleNet()

        v1 = net.getVertex("1")
        v2 = net.getVertex("2")
        v4 = net.getVertex("4")
        v3 = net.getVertex("3")
        v5 = net.getVertex("5")

        av = set([v for v in v5.iterAdjacentVertices()])
        assert len(av) == 4
        assert v1 in av
        assert v2 in av
        assert v3 in av
        assert v4 in av
        assert v5 not in av

    def test_isShapePoint(self):

        net = getSimpleNet()
        v7 = net.getVertex("7")

        assert not v7.isShapePoint()
        
        v9 = Vertex("9", 1200, 300)
        net.addVertex(v9)

        assert not v7.isShapePoint()

        e79 = Edge(v7, v9, 1)
        net.addEdge(e79)

        assert not v7.isShapePoint()

        e97 = Edge(v9, v7, 1)
        net.addEdge(e97)

        assert v7.isShapePoint()
        
