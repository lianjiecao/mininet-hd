from mininet.topo import Topo
from ripl.dctopo import FatTreeTopo
from jellyfish import JellyFish
from fatTree import FatTree as binaryTree
# from mininet.topolib import TreeTopo
import simulatorFunc

class ThreeTierTopo(Topo):

    def __init__(self, coreSw=4, fanout=4, hFanout=2, speed=1.0):
        super(ThreeTierTopo, self).__init__()

        self.nCoreSw = coreSw
        self.nAggSw = coreSw*fanout
        self.nEdgSw = self.nAggSw*fanout
        self.nHost = self.nEdgSw*hFanout
        # fanout = coreSw

        # core = StructuredNodeSpec(0, aggSw*fanout, None, speed, type_str = 'core')
        # agg = StructuredNodeSpec(aggSw*fanout, fanout, speed, speed, type_str = 'agg')
        # edge = StructuredNodeSpec(fanout, fanout, speed, speed, type_str = 'edge')
        # host = StructuredNodeSpec(1, 0, speed, None, type_str = 'host')
        # node_specs = [core, agg, edge, host]
        # edge_specs = [StructuredEdgeSpec(speed)] * 3
        # super(FatTreeTopo, self).__init__(node_specs, edge_specs)

        
        self.coreSw = []
        self.aggSw = []
        self.edgSw = []
        # Create core switches
        for c in range(self.nCoreSw):
            coreId = '%i_%i_%i' % (0, c, 0)
            self.coreSw.append(coreId)
            opt = self.genNodeOpt(0, c, 0)
            self.addSwitch(coreId, **opt)
            # Create aggregation switches
            for a in range(fanout):
                aggId = '%i_%i_%i' % (1, c, a)
                self.aggSw.append(aggId)
                opt = self.genNodeOpt(1, c, a)
                self.addSwitch(aggId, **opt)
                # Create edge switches, hosts and connect them
                for e in range(fanout):
                    edgCount = a*fanout+e
                    edgId = '%i_%i_%i' % (2, c, edgCount)
                    self.edgSw.append(edgId)
                    opt = self.genNodeOpt(2, c, edgCount)
                    self.addSwitch(edgId, **opt)
                    # Create hosts
                    for h in range(hFanout):
                        hostCount = edgCount*hFanout+h
                        hostId = '%i_%i_%i' % (3, c, hostCount)
                        opt = self.genNodeOpt(3, c, hostCount)
                        self.addHost(hostId, **opt)
                        # Connect hosts to edge switches
                        self.addLink(hostId, edgId)


        # Connect core switches and aggregation switches
        for csw in self.coreSw:
            for asw in self.aggSw:
                self.addLink(csw, asw)

        # Connect aggregation switches and edge switches
        for asw in self.aggSw:
            aswTr = int(asw.split('_')[1])
            # print '---agg sw:', asw
            for esw in self.edgSw:
                eswTr = int(esw.split('_')[1])
                # if fanout*aswId <= eswId and eswId < fanout*(aswId + 1):
                if aswTr == eswTr:
                    # print '   edg sw:', esw
                    self.addLink(asw, esw)


    def genNodeOpt(self, layer, sw, hs):
        '''Return MAC string'''
        opt = {}
        if layer == 3:
        # Hosts
            opt.update({'ip': "10.%i.%i.%i" % (layer, sw, hs)})
            opt.update({'mac': "00:00:00:%02x:%02x:%02x" % (layer, sw, hs)})
        else:
        # Switches
            dpidv = "%016x" %(((layer*10+sw) << 8) + 1)
            opt['dpid'] = dpidv
            # opt.update({'dpid': dpidv})

        return opt

class ClosTopo(Topo):

    def __init__(self, nPod, nCorePlane=2):
        super(ClosTopo, self).__init__()
        self.nAggSw = nCorePlane
        self.nEdgSw = 4
        self.nHost = 2*self.nEdgSw
        self.nCorePlane = nCorePlane
        self.nPod = nPod
        self.coreSw = []
        self.aggSw = []
        self.edgSw = []

        # switch id: x_y_z (layer_coreplane/pod_swID)
        # Create core swiches in each plane
        for cp in range(self.nCorePlane):
            for i in range(self.nPod):
                coreId = '%d_%d_%d' % (0, cp, i)
                self.coreSw.append(coreId)
                opt = self.genNodeOpt(0, cp, i)
                self.addSwitch(coreId, **opt)

        # Create aggregation swiches and edge swiches in each pod
        for p in range(self.nPod):
            tmpAgg = []
            for i in range(self.nAggSw):
                aggId = '%d_%d_%d' % (1, p, i)
                self.aggSw.append(aggId)
                tmpAgg.append(aggId)
                opt = self.genNodeOpt(1, p, i)
                self.addSwitch(aggId, **opt)
            for j in range(self.nEdgSw):
                edgId = '%d_%d_%d' % (2, p, j)
                self.edgSw.append(edgId)
                opt = self.genNodeOpt(2, p, j)
                self.addSwitch(edgId, **opt)
                # Connect aggregation swiches and edge swiches in the same pod
                for agg in tmpAgg:
                    self.addLink(edgId, agg)
                for h in range(self.nHost):
                    hostId = '%d_%d_%d' % (3, p, h)
                    opt = self.genNodeOpt(3, p, h)
                    self.addHost(hostId, **opt)
                    self.addLink(edgId, hostId)


        for csw in self.coreSw:
            for asw in self.aggSw:
                if csw.split('_')[1] == asw.split('_')[2]:
                    self.addLink(csw, asw)


    def genNodeOpt(self, layer, sw, hs):
        '''Return MAC string'''
        opt = {}
        if layer == 3:
        # Hosts
            opt.update({'ip': "10.%i.%i.%i" % (layer, sw, hs)})
            opt.update({'mac': "00:00:00:%02x:%02x:%02x" % (layer, sw, hs)})
        else:
        # Switches
            dpidv = "%016x" %(((layer*10+sw) << 8) + 1)
            opt['dpid'] = dpidv
            # opt.update({'dpid': dpidv})

        return opt

class RocketFuel(Topo):
    def __init__(self, file):
        super(RocketFuel, self).__init__()

        cont = open(file, 'r').read()
        entries = cont.split('\n')[:-1]
        sws = {}

        sw_map = {} # Map the old switch index to a set of continuous indexes starting from 1
        # Add switches
        i = 1
        for e in entries:
            tokens = e.split()
            sw_idx = str(i)
            sw_name = 's' + sw_idx
            sw_map[tokens[0]] = sw_name
            self.addSwitch(sw_name)
            # Add host to non-backbone switches
            if tokens[1] == 'nbb':
                h_name = 'h' + sw_idx
#                self.addHost(h_name, ip='10.0.0.'+str(sw_idx), cpu=0.1)
#                self.addLink(sw_name, h_name, bw=100, delay='1ms')
            if len(tokens) > 2:
                # bb = backbone, nb = neighbor
                sws[sw_name] = {'bb':tokens[1], 'nb':tokens[2:]}
            else:
                sws[sw_name] = {'bb':tokens[1], 'nb':''}
            i += 1
        # Add links
        l = []
        for sw in sws:
            if sws[sw]['nb']:
                for n in sws[sw]['nb']:
                    if sorted([sw, sw_map[n]]) not in l and sw != sw_map[n]:
                        if sws[sw]['bb'] == 'bb' and sws[sw_map[n]]['bb'] == 'bb':
                            self.addLink(sw, sw_map[n], bw=150, delay='1ms')
#                            self.addLink(sw, sw_map[n], bw=40, delay='1ms')
                        else:
                            self.addLink(sw, sw_map[n], bw=150, delay='1ms')
#                            self.addLink(sw, sw_map[n], bw=10, delay='1ms')
                        l.append(sorted([sw, sw_map[n]]))

class TopoSet:
    def __init__(self, nSw, typeTopo='all', nTopo=1):
        
        self.type = typeTopo.lower()
        self.num = nTopo
        self.nSw = nSw
        if self.type == 'all':
            self.topos = {'fattree':[], 'jellyfish':[], 'clos':[], 'rocketfuel':[]}
        else:
            self.topos = {self.type:[]}
        # self.nHost = 64
        # self.nSw = 5*self.nPod**2/4
        # self.k = 4
        self.bw = 10
        self.rfTopos = {
           318:'1221.r0.cch.abr',
           604:'1239.r0.cch.abr',
           172:'1755.r0.cch.abr',
           960:'2914.r0.cch.abr',
           240:'3257.r0.cch.abr',
           624:'3356.r0.cch.abr',
           201:'3967.r0.cch.abr',
            11:'4755.r0.cch.abr',
           631:'7018.r0.cch.abr'
        }


    def genTopo(self):

        for i in range(self.num):
            # if self.type == 'threetier' or self.type == 'all':
            #     t = ThreeTierTopo(int(round(self.nSw/12)))
            #     for link in t.links():
            #         t.setlinkInfo(link[0], link[1], {"bw":self.bw, "delay":"1"})
            #     self.topos['threetier'].append(t)
            if self.type == 'clos' or self.type == 'all':
                t = ClosTopo(int(round(self.nSw/8)))
                for link in t.links():
                    t.setlinkInfo(link[0], link[1], {"bw":self.bw, "delay":"1"})
                self.topos['clos'].append(t)

            k = int(round((0.8*self.nSw)**0.5))
            if self.type == 'fattree' or self.type == 'all':
                t = FatTreeTopo(k)
                for link in t.links():
                    t.setlinkInfo(link[0], link[1], {"bw":self.bw, "delay":"1"})
                self.topos['fattree'].append(t)
                self.nHost = int(len(t.switches())/1.2)
                # self.k = len(t.links())/len(t.switches())+1
                
                # self.bw = 10
            # if self.type == 'binarytree' or self.type == 'all':
            #     self.topos.append(binaryTree(self.nHost, self.bw, 0.1))
            
            if self.type == 'jellyfish' or self.type == 'all':
                self.topos['jellyfish'].append(JellyFish(self.nHost, self.nSw, int(0.2*self.nSw), self.bw*2, lat=0.1))
                # JellyFish(nHost, nSw, k, bw, lat=0.1)
            # if self.type == 'treenet' or self.type == 'all':
            #     t = TreeTopo(3, 2)
            #     for link in t.links():
            #         t.setlinkInfo(link[0], link[1], {"bw":self.bw, "delay":"1"})
            #     self.topos.append(t)
            if self.type == 'rocketfuel' or self.type == 'all':
                rfFile = '../rocketfuel/sigcomm02/' + self.selectRF(self.nSw)
                self.topos['rocketfuel'].append(RocketFuel(rfFile))


    def selectRF(self, n):
        diff = {abs(n-x):x for x in self.rfTopos}
        sortDiff = sorted(diff)
        return self.rfTopos[diff[sortDiff[0]]]

    def getTopoWKey(self):
        return self.topos

    def getTopo(self):
        tmp = []
        for i in self.topos:
            tmp = tmp + self.topos[i]
        return tmp



if __name__ == '__main__':
    for i in range(100, 1001, 100):
        print '\n', i
        t = TopoSet(i, typeTopo='rocketfuel')
        t.genTopo()
        for topo in t.getTopo():
            # print topo.switches()
            simulatorFunc.checkTopo(topo)
            # print topo.switches(), topo.links()
            # print topo.links()
        # t = ThreeTierTopo(i)
        # for link in t.links():
        #     t.setlinkInfo(link[0], link[1], {"bw":10, "delay":1})
        # simulatorFunc.checkTopo(t)
        # for s in t.switches():
        #     print s
        # print t.hosts()
        # print [x for x in t.links() if '1_0_0' in x]
