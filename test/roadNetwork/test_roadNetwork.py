__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import nose.tools

from roadNetwork.graph import Graph
from roadNetwork.vertex import Vertex
from roadNetwork.edge import Edge
from roadNetwork.errors import GraphError
from roadNetwork.test.simpleNetworks import getSimpleNet

def getSimpleGraph():

    v1 = Vertex("1", 0, 100)
    v2 = Vertex("2", 100, 200)
    v3 = Vertex("3", 100, 0)
    v4 = Vertex("4", 200, 100)
    v5 = Vertex("5", 100, 100) 
    v6 = Vertex("6", 200, 200)
    v7 = Vertex("7", 300, 100)
    v8 = Vertex("8", 200, 0)

    graph = Graph("test", 0, 60, 5)
    graph.addVertex(v1)
    graph.addVertex(v2)
    graph.addVertex(v3)
    graph.addVertex(v4)
    graph.addVertex(v5)
    graph.addVertex(v6)
    graph.addVertex(v7)
    graph.addVertex(v8)


#
#                2         6
#                |         |
#                |         |
#      1 ------- 5 ------- 4 -------- 7
#                |         |
#                |         |
#                |         |
#                3         8
#


    e15 = Edge(v1, v5, 3)
    e51 = Edge(v5, v1, 2)
    e35 = Edge(v3, v5, 3)
    e53 = Edge(v5, v3, 2)
    e45 = Edge(v4, v5, 2)
    e54 = Edge(v5, v4, 3)
    e52 = Edge(v5, v2, 2)
    e25 = Edge(v2, v5, 3)

    e48 = Edge(v4, v8, 2)
    e84 = Edge(v8, v4, 3)
    e74 = Edge(v7, v4, 3)
    e47 = Edge(v4, v7, 2)
    e46 = Edge(v4, v6, 2)
    e64 = Edge(v6, v4, 3)

    edges = [e15, e51, e35, e53, e45, e54, e52, e25, e48, e84, e74, e47, 
             e46, e64]

    graph.addEdge(e15)
    graph.addEdge(e51)
    graph.addEdge(e35)
    graph.addEdge(e53)
    graph.addEdge(e45)
    graph.addEdge(e54)
    graph.addEdge(e52)
    graph.addEdge(e25)
    graph.addEdge(e48)
    graph.addEdge(e84)
    graph.addEdge(e74)
    graph.addEdge(e47)
    graph.addEdge(e46)
    graph.addEdge(e64)

    return graph


class TestGraph:

    def test_construction(self):

        g = getSimpleGraph()

        assert g.getNumVertices() == 8
        assert g.getNumEdges() == 14
            

    def test_getVertex(self):
        
        g = getSimpleGraph()

        v1 = g.getVertex("1")
        assert v1.id == "1"

        nose.tools.assert_raises(GraphError, g.getVertex, "128")
        
    def test_getEdge(self):
        
        g = getSimpleGraph()

        e15 = g.getEdge("1", "5")

        assert e15.iid == ("1", "5")

        nose.tools.assert_raises(GraphError, g.getEdge, "1", "128")
        nose.tools.assert_raises(GraphError, g.getEdge, "199", "128")

    def test_hasVertex(self):
        
        g = getSimpleGraph()

        assert g.hasVertex("1")

        assert not g.hasVertex('2342')

    def test_hasEdge(self):
        
        g = getSimpleGraph()

        assert g.hasEdge('1', '5')

        assert not g.hasEdge("100", "200")

    def test_iterVertices(self):
        
        g = getSimpleGraph()

        result = [v.id for v in g.iterVertices()]

        answer = map(str, range(1, 9))
        assert result == answer

    def test_iterEdges(self):

        g = getSimpleGraph()
        answer = ['1 5', '5 1', '3 5', '5 3', '4 5', '5 4', '5 2', 
                  '2 5', '4 8', '8 4', '7 4', '4 7', '4 6', '6 4']
        
        result = [edge.iid_ for edge in g.iterEdges()]

        assert answer == result

    def test_deleteEdge(self):
        
        net = getSimpleNet() 

        edge15 = net.getEdge("1", "5")
        edge25 = net.getEdge("2", "5") 
        edge47 = net.getEdge("4", "7") 

        assert edge15.hasOutMovement("4")
        assert edge25.hasOutMovement("4")
        assert edge47.hasInMovement("5") 
        edge54 = net.getEdge("5", "4") 

        net.deleteEdge(edge54)

        assert not edge15.hasOutMovement("4")
        assert not edge25.hasOutMovement("4")
        assert not edge47.hasInMovement("5") 
        
        assert not net.hasEdge("5", "4") 

    def test_deleteVertex(self):

        net = getSimpleNet() 

        v5 = net.getVertex("5")

        net.deleteVertex(v5) 

        assert not net.hasEdge("1", "5")
        assert not net.hasEdge("2", "5") 
        assert not net.hasVertex("5") 

    def test_splitEdge(self):

        net = getSimpleNet() 
        edge = net.getEdge("5", "4") 

        edgesBefore = net.getNumEdges() 
        verticesBefore = net.getNumVertices()
        net.splitEdge(edge)
        assert net.getNumEdges() == edgesBefore + 1
        assert net.getNumVertices() == verticesBefore + 1 

        #netViewer(net)
