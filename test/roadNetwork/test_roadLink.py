__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

import nose.tools

from roadNetwork.vertex import Vertex
from roadNetwork.edge import Edge
from roadNetwork.movement import Movement
from roadNetwork.test.simpleNetworks import constructIntersection, getSimpleNet
from roadNetwork.errors import GraphError, SimError


class TestEdge:

    def test_construction(self):

        v1 = Vertex("1", 1.0, 1.0)
        v2 = Vertex("2", 2.0, 2.0)

        edge12 = Edge(v1, v2, 3)

        assert edge12.getNumLanes() == 3

        assert edge12.getNumOutMovements() == 0
        assert edge12.getNumInMovements() == 0

        assert not edge12.hasOutMovement("33")
        assert not edge12.hasInMovement("2345")

    def NOtest_addOutMovementRaises(self):

        v5 = constructIntersection()


        e53 = v5.getOutEdge("3")
        e51 = v5.getOutEdge("1")
        e52 = v5.getOutEdge("2")
        e54 = v5.getOutEdge("4")
        
        e35 = v5.getInEdge("3")
        e45 = v5.getInEdge("4")
        e25 = v5.getInEdge("2")
        e15 = v5.getInEdge("1")


        #mov1525 = Movement(e15, e25, 0, 0, 1)
        #nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1525))
        mov1552 = Movement(e15, e52, 1)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))
        #e15.addOutMovement(mov1552)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e25, 0, 0, 1)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 3, 0, 1)
#

        mov1552 = Movement(e15, e52, 2)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))
        mov1552 = Movement(e15, e52, 3)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))
        mov1552 = Movement(e15, e52, 4)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))
        
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 2, 0, 2)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 1, 0, 3)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 0, 0, 4)
#
        mov1552 = Movement(e15, e52, 3)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))

        mov1552 = Movement(e15, e52, 2)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))

        mov1552 = Movement(e15, e52, 1)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))

#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 0, 0, 3)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 0, 1, 2)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 0, 2, 1)
#
        mov1552 = Movement(e15, e52, 0)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))
        mov1552 = Movement(e15, e52, -1)
        nose.tools.assert_raises(GraphError, e15.addOutMovement(mov1552))

#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, -1, 0, 1)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 0, -1, 1)
#        nose.tools.assert_raises(GraphError, e15.addOutMovement, e52, 0, 0, -1)
        
    def test_addOutMovement(self):
        
        v5 = constructIntersection()


        e53 = v5.getOutEdge("3")
        e51 = v5.getOutEdge("1")
        e52 = v5.getOutEdge("2")
        e54 = v5.getOutEdge("4")
        
        e35 = v5.getInEdge("3")
        e45 = v5.getInEdge("4")
        e25 = v5.getInEdge("2")
        e15 = v5.getInEdge("1")

        
        #nose.tools.assert_raises(GraphError, e15.addOutMovement, e25, 0, 0, 1)
                       
        assert not  e15.hasOutMovement("2")

        #add a left turn
        mov152 = Movement(e15, e52, 1)
        e15.addOutMovement(mov152)
        #try to add it again
        nose.tools.assert_raises(GraphError, e15.addOutMovement, mov152)
        assert e15.hasOutMovement("2")

        #add a right turn
        assert not e15.hasOutMovement("3")
        mov153 = Movement(e15, e53, 1)
        e15.addOutMovement(mov153)
        assert e15.hasOutMovement("3")

        
        #add a through turn
        mov154 = Movement(e15, e54, 2)
        #e15.addOutMovement(e54, 1, 0, 2)
        e15.addOutMovement(mov154)
        assert e15.hasOutMovement("4")        

    def test_iterOutMovements(self):
        
        
        v5 = constructIntersection(withMovements=True)

        e15 = v5.getInEdge("1")
        e53 = v5.getOutEdge("3")
        e51 = v5.getOutEdge("1")
        e52 = v5.getOutEdge("2")
        e54 = v5.getOutEdge("4")


        result = [mov.iid_ for mov in e15.iterOutMovements()] 
        
        answer = ['1 5 2', '1 5 4', '1 5 3']

        assert result == answer


    def test_hasInMovement(self):

        v5 = constructIntersection(withMovements=True)

        e15 = v5.getInEdge("1")
        e53 = v5.getOutEdge("3")
        e51 = v5.getOutEdge("1")
        e52 = v5.getOutEdge("2")
        e54 = v5.getOutEdge("4")
                
        e52.hasInMovement("1")
        e53.hasInMovement("1")
        e54.hasInMovement("1")
        
    def test_deleteOutMovement(self):
        
        v5 = constructIntersection(withMovements=True)

        e15 = v5.getInEdge("1")
        e53 = v5.getOutEdge("3")
        e51 = v5.getOutEdge("1")
        e52 = v5.getOutEdge("2")
        e54 = v5.getOutEdge("4")
                 
        mov152 = e15.getOutMovement("2")
        mov154 = e15.getOutMovement("4")
        mov153 = e15.getOutMovement("3")

        assert e15.hasOutMovement("2")
        assert e52.hasInMovement("1")
        assert e15.getNumOutMovements() == 3
        assert e52.getNumInMovements() == 1
        e15.deleteOutMovement(mov152)
        assert not e15.hasOutMovement("2")
        assert not e52.hasInMovement("1")
        assert e15.getNumOutMovements() == 2
        assert e52.getNumInMovements() == 0

    def test_getAcuteAngle(self):

        v5 = constructIntersection(withMovements=True)

        e15 = v5.getInEdge("1")
        e52 = v5.getOutEdge("2")
        e25 = v5.getInEdge("2")
        e35 = v5.getInEdge("3")
        e54 = v5.getOutEdge("4")
        e45 = v5.getInEdge("4")
        
        assert e15.getAcuteAngle(e52) == 90
        assert e52.getAcuteAngle(e15) == 90

        assert e15.getAcuteAngle(e54) == 180
        assert e15.getAcuteAngle(e45) == 180

        net = getSimpleNet()

        v5 = net.getVertex("5")
        v8 = net.getVertex("8")

        e58 = Edge(v5, v8, 3)
        net.addEdge(e58)

        e15 = net.getEdge("1", "5")
        e51 = net.getEdge("5", "1")

        assert e15.getAcuteAngle(e58) == 135
        assert e51.getAcuteAngle(e58) == 135

        assert e58.getAcuteAngle(e15) == 135
        assert e58.getAcuteAngle(e51) == 135

        e85 = Edge(v8, v5, 2)
        net.addEdge(e85)

        assert e15.getAcuteAngle(e85) == 135
        assert e51.getAcuteAngle(e85) == 135

        assert e85.getAcuteAngle(e15) == 135
        assert e85.getAcuteAngle(e51) == 135

    def test_angle(self):
        
        v5 = constructIntersection(withMovements=True)

        e15 = v5.getInEdge("1")
        e51 = v5.getOutEdge("1")
        e52 = v5.getOutEdge("2")
        e25 = v5.getInEdge("2")
        e35 = v5.getInEdge("3")
        e54 = v5.getOutEdge("4")
        e45 = v5.getInEdge("4")
        
        assert e15.getAngleClockwise(e52) == 90
        assert e51.getAngleClockwise(e52) == 270

        assert e45.getAngleClockwise(e52) == 270
        assert e54.getAngleClockwise(e52) == 90

        assert e25.getAngleClockwise(e54) == 90
        assert e25.getAngleClockwise(e45) == 270

        assert e45.getAngleClockwise(e35) == 270
        assert e54.getAngleClockwise(e35) == 90
        #assert e54.getAngleClockwise(e52) == 90
        
        assert e15.getAngleClockwise(e15) == 0
        assert e15.getAngleClockwise(e51) == 180

    def createNet(self):

        net = getSimpleNet()

        link15 = net.getEdge('1', '5')

        mov152 = link15.getOutMovement('2')
        mov152.setSimVolume(0, 5, 1)
        mov152.setSimTTInMin(0, 5, 1)
        mov152.setSimVolume(5, 10, 3)

        mov152.setSimTTInMin(5, 10, 4)
        mov152.setObsCount(0, 5, 11)
        mov152.setObsCount(5, 10, 11)
        
        mov154 = link15.getOutMovement('4')
        mov154.setSimVolume(0, 5, 2)
        mov154.setSimTTInMin(0, 5, 2)
        mov154.setSimVolume(5, 10, 5)
        mov154.setSimTTInMin(5, 10, 6.3)
        mov154.setObsCount(0, 5, 7)
        mov154.setObsCount(5, 10, 11)

        mov153 = link15.getOutMovement('3')
        mov153.setSimVolume(0, 5, 3)
        mov153.setSimTTInMin(0, 5, 3)
        mov153.setSimVolume(5, 10, 5)
        mov153.setSimTTInMin(5, 10, 8.9)
        mov153.setObsCount(0, 5, 43)
        mov153.setObsCount(5, 10, 23)

        link25 = net.getEdge('2', '5')
        link25.setObsCount(0, 5, 10)
        link25.setObsCount(5, 10, 20)

        return net, link15, link25

    def test_hasCountInfo(self):
        
        net, link15, link25 = self.createNet()

        assert link25.hasCountInfo()
        assert link15.hasCountInfo()

        link35 = net.getEdge('3', '5')

        assert not link35.hasCountInfo()

        link53 = net.getEdge('5', '3')

        assert not link53.hasCountInfo()

        mov351 = link35.getOutMovement('1')
        mov352 = link35.getOutMovement('2')
        mov354 = link35.getOutMovement('4')

        mov351.setObsCount(0, 5, 1)
        mov352.setObsCount(0, 5, 2)

        assert not link35.hasCountInfo()

        #TODO: the following assertion should fail
        mov354.setObsCount(5, 10, 3)
        assert  link35.hasCountInfo()

    def test_getObsCount(self):
        
        net, link15, link25 = self.createNet()

        assert link25.getObsCount(0, 5) == 10
        assert link25.getObsCount(0, 10) == 30

        assert link15.getObsCount(0, 5) == 43 + 7 + 11
        assert link15.getObsCount(5, 10) == 11 + 11 + 23
        assert link15.getObsCount(0, 10) == link15.getObsCount(0, 5) + link15.getObsCount(5, 10)
        
    def test_setObsCount(self):

        net, link15, link25 = self.createNet()
        assert link15.getObsCount(0, 5) == 43 + 7 + 11        
        nose.tools.assert_raises(SimError, link15.setObsCount, 0, 5, 15)
        assert link15.getObsCount(0, 5) == 43 + 7 + 11

    def test_setObsCount2(self):

        net, link15, link25 = self.createNet()

        link25.setObsCount(40, 50, 0)
        nose.tools.assert_raises(SimError, link25.setObsCount, 40, 50, -1)

    def test_iterCountPeriods(self):
        
        net, link15, link25 = self.createNet()

        result = list(link15.iterCountPeriods())
        answer = [(0, 5), (5, 10)]
        assert result == answer

        result = list(link25.iterCountPeriods())
        assert result== answer
        assert [] == sorted(net.getEdge('8', '4').iterCountPeriods())

        result = list(link15.iterCountPeriods(timeStepInMin=5))
        answer = [(0, 5), (5, 10)]
        assert result == answer

        result = list(link15.iterCountPeriods(timeStepInMin=10))
        answer = [(0, 10)]
        assert result == answer

    def test_getSimVolume(self):
        
        net, link15, link25 = self.createNet()
        assert link15.getSimVolume(0, 5) == 6
        assert link15.getSimVolume(5, 10) == 13

    def test_getSimVolumeErrors(self):

        net, link15, link25 = self.createNet()
        nose.tools.assert_raises(SimError, link15.getSimVolume, 0, 125)

    def test_getSimFlow(self):

        net, link15, link25 = self.createNet()    

        assert link15.getSimFlow(0, 10) == (6 + 13) * 6
        assert link15.getSimFlow(0, 20) == (6 + 13) *  3
  
        link84 = net.getEdge('8', '4')
        assert link84.getSimFlow(0, 5) == 0
    
    def test_setSimVolumeAndGetSimFlow(self):
        
        net, link15, link25 = self.createNet()        

        #this is a boundry link with no emanating movements
        link51 = net.getEdge("5", "1")

        link51.setSimVolume(0, 5, 10)
        link51.setSimVolume(5, 10, 20)

        link51.setSimVolume(20, 25, 30)

        assert link51.getSimFlow(0, 5) == 10 * 12
        assert link51.getSimFlow(5, 10) == 20 * 12
        assert link51.getSimFlow(0, 10) == 30 * 6 
        assert link51.getSimFlow(0, 20) == 30 * 3
        assert link51.getSimFlow(0, 30) == 60 * 2
        
        
