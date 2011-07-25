__author__ = "Michail Xyntarakis"
__company__ = "Parsons Brinckerhoff"
__email__ = "xyntarakis@pbworld.com"
__license__ = "GPL"

from roadNetwork.test.simpleNetworks import getSimpleNet
from roadNetwork.errors import SimError

import nose.tools

def addSimVolumeToNet(net):

    v = net.getVertex("5")
    sMov = v.getMovement("1", "4")

    sMov.setSimVolume(0, 5, 1)
    sMov.setSimVolume(5, 10, 2)
    sMov.setSimVolume(10, 15, 3)
    sMov.setSimVolume(15, 20, 4)

    sMov.setSimTTInMin(0, 5, 1)
    sMov.setSimTTInMin(5, 10, 2)
    sMov.setSimTTInMin(10, 15, 3)

    sMov.setObsCount(0, 5 , 2)
    sMov.setObsCount(5, 10, 3)
    sMov.setObsCount(10, 15, 4)
    sMov.setObsCount(15, 20, 5)
        
    return net

class TestMovement:

    def test_simFlow(self):

        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")

        assert sMov.getSimFlow(0, 5) == 1 * 12
        assert sMov.getSimFlow(0, 10) == (1 + 2) * 6
        assert sMov.getSimFlow(5, 20) == (2 + 3 + 4) * 4
        assert sMov.getSimFlow(0, 20) == (1 + 2 + 3 + 4) * 3.0
        assert sMov.getSimFlow(0, 30) == (1 + 2 + 3 + 4) * 2.0

    def test_simMeanTT(self):

        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")

        assert sMov.getSimTTInMin(0, 5) == 1 
        assert sMov.getSimTTInMin(0, 10) == (1 + 4) / 3.0
        assert sMov.getSimTTInMin(5, 15) == (2 * 2 + 3 * 3) / 5.0

        nose.tools.assert_raises(SimError, sMov.getSimTTInMin, 0, 30)
        nose.tools.assert_raises(SimError, sMov.getSimTTInMin, 30, 0)

        sMov.setSimTTInMin(15, 20, 4)
        assert sMov.getSimTTInMin(0, 30) == (1*1 + 2*2 + 3*3 + 4*4) / 10.0
                
    def testSimTTInMin(self):

        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")

        link51 = net.getEdge("5", "1") 
        assert link51.lengthInFeet == 300
        assert link51.lengthInMiles == 300 / 5280.0
        #nose.tools.set_trace()
        assert sMov.getSimTTInMin(30, 40) == link51.lengthInMiles / link51.freeFlowSpeedInMPH * 60

    def test_getObsCount(self):
        """Obs counts have the same time step with the simResults"""
        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")
   
        assert sMov.getObsCount(0, 5) == 2
        assert sMov.getObsCount(0, 10) == 5
        assert sMov.getObsCount(10, 20) == 9

        assert not sMov.getObsCount(0, 30)
    
    def test_getObsCounts2(self):
        """Obs counts use a time step different than that of the simResults"""

        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")
        sMov2 = net.getVertex("4").getMovement("5", "8")
    
        sMov2.setObsCount(0, 10, 7)
        sMov2.setObsCount(10, 20, 13)
        sMov2.setObsCount(20, 30, 14)

        assert sMov2.getObsCount(0, 10) == 7
        assert sMov2.getObsCount(0, 20) == 20
        assert sMov2.getObsCount(0, 30) == 34

    def test_hasObsCount(self):

        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")

        assert sMov.hasObsCount(0, 5)
        assert not sMov.hasObsCount(0, 30)

    def test_setObsCount(self):

        net = getSimpleNet()
        addSimVolumeToNet(net)
        sMov = net.getVertex("5").getMovement("1", "4")

        
        sMov.setObsCount(0, 15, 0)
        nose.tools.assert_raises(SimError, sMov.setObsCount, 0, 15, -1)
        
        
