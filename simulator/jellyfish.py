import sys, random,re

from ripl.dctopo import JellyFishTopo
from mininet.topo import Topo

class JellyFish(Topo):
    def randByte(self):
        return hex(random.randint(0,255))[2:]

    def makeMAC(self, i):
        return self.randByte()+":"+self.randByte()+":"+self.randByte()+":00:00:" + hex(i)[2:]
    
    def makeDPID(self, i):
        a = self.makeMAC(i)
        dp = "".join(re.findall(r'[a-f0-9]+',a))
        return "0" * ( 12 - len(dp)) + dp
    
    # args is a string defining the arguments of the topology! has be to format: "x,y,z" to have x hosts and a bw limit of y for those hosts each and a latency of z (in ms) per hop
    def __init__(self, hosts=2, sw=10, k=3, bwlimit=10, lat=0.1, **opts):
        Topo.__init__(self, **opts)
        t = JellyFishTopo(0, sw, hosts, k)
        numLeafes = hosts
        bw = bwlimit

#        for i in range(1, len(t.hosts()) + 1):
        i = 1
        for ht in t.hosts():
            hName = ht[0] + str(int(ht[1:]) + 1)
            h = self.addHost(hName, mac=self.makeMAC(i), ip="10.0.0." + str(i))
            i += 1
#            h = self.addHost('h' + str(i), mac=self.makeMAC(i), ip="10.0.0." + str(i))
            
#        for i in range(1, len(t.switches()) + 1):
        i = 1
        for swh in t.switches():
            swName = swh[0] + str(int(swh[1:]) + 1)
            sw = self.addSwitch(swName, dpid=self.makeDPID(i),  **dict(listenPort=(13000+i-1)))
            i += 1
#            sw = self.addSwitch('s' + str(i), dpid=self.makeDPID(i),  **dict(listenPort=(13000+i-1)))
#            self.addLink(h, sw, bw=bw, delay=str(lat) + "ms")
#            tor.append(sw)

        for link in t.links():
#            print link, link[0][1:-1]
            end_1 = link[0][0] + str(int(link[0][1:]) + 1)
            end_2 = link[1][0] + str(int(link[1][1:]) + 1)
            self.addLink(end_1, end_2, bw=bw, delay=str(lat) + "ms")

#        toDo = tor  # nodes that have to be integrated into the tree

#        while len(toDo) > 1:
#            newToDo = []
#            for i in range(0, len(toDo), 2):
#                sw = self.addSwitch('s' + str(s), dpid=self.makeDPID(s), **dict(listenPort=(13000+s-1)))
#                s = s+1
#                newToDo.append(sw)
#                self.addLink(toDo[i], sw, bw=bw, delay=str(lat) + "ms")
#                if len(toDo) > i+1:
#                    self.addLink(toDo[i+1], sw, bw=bw, delay=str(lat) + "ms")
#            toDo = newToDo
#            bw = 2.0*bw
            
