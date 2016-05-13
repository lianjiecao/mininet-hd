import subprocess, os, logging, time
from mininet.log import setLogLevel, debug, info, error
from mininet.topo import Topo, LinearTopo
from cluster import Placer, RoundRobinPlacer, RandomPlacer, SwitchBinPlacer, HostSwitchBinPlacer
# the following block is to support deprecation warnings. this is really not
# solved nicely and should probably be somewhere else
import warnings, sys
import functools
from math import ceil, log
from random import randrange

import simulatorFunc
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logging.basicConfig()

class Cluster:
    def __init__(self, topologies, tunnels):
        self.topos = topologies
        self.tunnels = tunnels
    
    def getTunnels(self):
        return self.tunnels

    def getTopos(self):
        return self.topos


class Partitioner:
    """
    Use metis with vertex and edge weight
    """

    def __init__(self, topo, tool=''):

        """
        Initialize all data structures that may be used in the partitioning process.
        """
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.toolCMD = tool
        self.topo = topo
        self.pos = {}
        self.switches = {}
        self.hostToSw = {}
        self.nodeToPart = {}
        self.tunnels = []
        self.partitions = []
        self.graphFile = [[]] # <-- index 0 is header
        i = 1
        # Replace the original name of nodes with integers starting from 0 and 
        # record the mapping between original name and new name for later recovering
        for switch in topo.switches():
            self.switches[switch] = i
            self.pos[i] = switch
            self.graphFile.append([i, 0])
            i += 1
        self.swLinks = 0
        for link in topo.links():
            # For sw-sw links, store info in the format of [swName swWeight neighborSw_i edgeWeigth_i]
            # For host-sw links, store info for recovering subtopologies after partitioning
            if (topo.isSwitch(link[0]) and topo.isSwitch(link[1])): # Links between 2 switches
                # Add neighbors
                self.graphFile[self.switches[link[0]]] += [self.switches[link[1]],int(topo.linkInfo(link[0],link[1])["bw"])]
                self.graphFile[self.switches[link[1]]] += [self.switches[link[0]],int(topo.linkInfo(link[0],link[1])["bw"])]
                # Update vertex weight
                self.graphFile[self.switches[link[0]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.graphFile[self.switches[link[1]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.swLinks += 1
            elif topo.isSwitch(link[0]):
                self.graphFile[self.switches[link[0]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.hostToSw[link[1]] = link[0]
                # self.swToHost.setdefault(link[0], []).append(link[1])
            elif topo.isSwitch(link[1]):
                self.graphFile[self.switches[link[1]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.hostToSw[link[0]] = link[1]
                # self.swToHost.setdefault(link[1], []).append(link[0])

    def partition(self,n, alg="chaco", shares=None):
        """
        This function needs to be implemented for each specific partitioning algorithm
        """
        return Cluster(self.topo, self.tunnels)



class MetisPartitioner(Partitioner):
    """
    METIS Partitioner
    """
    def __init__(self, topo, tool=""):
        Partitioner.__init__( self, topo, tool="gpmetis -ptype=rb")


    def partition(self, n, alg="metis", shares=None):

        # Create input file for METIS, removing the first swName
        self.graphFile = [x[1:] for x in self.graphFile]
        self.graphFile[0] = [len(self.switches), self.swLinks, "011 0"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self._write_to_file(pstr)

        if n > 1 and len(self.switches) > 1:
            if shares:
                metisShares = simulatorFunc.calcMetisShare(self.topo, shares)
                tpw=""
                for i in range(0, n):
                    tpw += str(i) + " = " + str(metisShares[i]) + "\n"
                tpwf = self._write_to_file(tpw)
                outp = subprocess.check_output([self.toolCMD + " -tpwgts=" + tpwf + " " + self.graph + " " + str(n)], shell=True)
                os.remove(tpwf)
            else:
                startT = time.time()
                outp = subprocess.check_output([self.toolCMD + " " + self.graph + " " + str(n)], shell=True)
                # print "Metis-partition:", time.time()-startT
            self.logger.debug(outp)
            
            startT = time.time()
            self._parse_partition_result(self.graph + ".part." + str(n), n)
            #print "Metis-reconstruct:", time.time()-startT
            os.remove(self.graph + ".part." + str(n))
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)


    def _write_to_file(self, pstr):
        """
        Dump the graph to a file for graph partition tools
        """
        # pstr = ""
        # for line in self.graphFile:
        #     pstr = pstr + " ".join(map(str, line)) + "\n"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            filename = os.tempnam()
        self.logger.debug("Output file: " + filename)
        self.logger.debug(pstr)
        f = open(filename, "w")
        f.write(pstr)
        f.close()
        return filename


    def _parse_partition_result(self, filepath, n):

        for i in range(0, n):
            self.partitions.append(Topo())
        f = open(filepath, "r")
        i = 1

        # Add nodes from the output file
        for line in f:
            part = int(line)
            if part > n-1:
                part = n-1
            self.nodeToPart[self.pos[i]] = part
#            print 'part:', part, ',pos:', i, self.pos[i]
            self.partitions[part].addNode(self.pos[i], **self.topo.nodeInfo(self.pos[i]))
            i += 1
        f.close()
        startT = time.time()

        for hs in self.hostToSw:
            self.partitions[self.nodeToPart[self.hostToSw[hs]]].addNode(hs, **self.topo.nodeInfo(hs))
            self.partitions[self.nodeToPart[self.hostToSw[hs]]].addLink(hs, self.hostToSw[hs] , **self.topo.linkInfo(hs, self.hostToSw[hs]))

        #print "Metis-addNodes:", time.time()-startT
        startT = time.time()

        # Recover links and record tunnels
        for edge in self.topo.links():
            if (self.topo.isSwitch(edge[0]) and self.topo.isSwitch(edge[1])):
                if(self.nodeToPart[edge[0]] == self.nodeToPart[edge[1]]):
                    self.partitions[self.nodeToPart[edge[0]]].addLink(edge[0], edge[1], **self.topo.linkInfo(edge[0],edge[1]))
                else:
                    self.tunnels.append([edge[0],edge[1], self.topo.linkInfo(edge[0], edge[1])])
        #print "Metis-addLinks:", time.time()-startT
        self.logger.debug('Topologies:')
        for t in self.partitions:
            self.logger.debug('Partition ' + str(self.partitions.index(t)))
            self.logger.debug('Nodes: ' + str(t.nodes()))
            self.logger.debug('Links: ' + str(t.links()))
        self.logger.debug('Tunnels: ' + str(self.tunnels))


class ChacoPartitioner(MetisPartitioner):
    """
    Chaco partitioner with multilevel KL
    """

    def __init__(self, topo, tool='~/Chaco-2.2/exec/chaco'): 
        Partitioner.__init__( self, topo, tool)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"

    def partition(self, n, alg="chaco", shares=None):
        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self._write_to_file(pstr)

        inputPara = self.toolCMD+'.in'
        subprocess.call('echo "'+self.graph+'\n'+self.graph+'.out\n1\n50\n2\n2\nn\n" > '+inputPara, shell=True)
        subprocess.call('echo "'+self.chacoCtlPara+'" > User_Params', shell=True)
 
        if n > 1 and len(self.switches) > 1:
            startT = time.time()
            outp = subprocess.check_output(["cat "+inputPara+" | "+self.toolCMD], shell=True)
            #print "Chaco-partition:", time.time()-startT
            self.logger.debug(outp)
            startT = time.time()
            self._parse_partition_result(self.graph+".out",n)
            #print "Chaco-reconstruct:", time.time()-startT
            os.remove(self.graph+".out")
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)


class ChacoUEPartitioner(MetisPartitioner):
    """
    Chaco partitioner with multilevel KL
    """

    def __init__(self, topo, tool='~/Chaco-2.2-siyuan/exec/chaco'): 
        Partitioner.__init__( self, topo, tool)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"

    def partition(self, n, alg="chacoUE", shares=None):

        if shares is None:
            self.logger.info('Shares are invalid!')
            sys.exit(0)

        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self._write_to_file(pstr)

        inputPara = self.toolCMD+'.in'
        dim = int(ceil(log(n, 2)))
        caps = '\n'.join(map(str, shares+[0]*(2**dim-n)))

        subprocess.call('echo "'+self.graph+'\n'+self.graph+'.out\n1\n50\n'+str(dim)+'\n'+caps+'\n2\nn\n" > '
            +inputPara, shell=True)
        subprocess.call('echo "'+self.chacoCtlPara+'" > User_Params', shell=True)

        if n > 1 and len(self.switches) > 1:
            startT = time.time()
            outp = subprocess.check_output(["cat "+inputPara+" | "+self.toolCMD], shell=True)
            #print "Chaco-partition:", time.time()-startT
            self.logger.debug(outp)
            startT = time.time()
            self._parse_partition_result(self.graph+".out",n)
            #print "Chaco-reconstruct:", time.time()-startT
            os.remove(self.graph+".out")
#            print self.graph
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)


class MininetPartitioner(Partitioner):
    """
    Wrapper of Mininet placers
    """
    def __init__(self, topo, tool=''): 
        Partitioner.__init__( self, topo)
        self.placers = {'mn-random': RandomPlacer, 'mn-roundRobin': RoundRobinPlacer,
                'mn-switchBin':SwitchBinPlacer, 'mn-hostSwitchBin':HostSwitchBinPlacer}

    def partition(self, n, alg='mn-random', shares=None):

        self.alg = alg
        self.placer = self.placers[self.alg](servers=[x for x in range(n)], nodes=self.topo.nodes(), 
            hosts=self.topo.hosts(), switches=self.topo.switches(), links=self.topo.links())
        # Create subtopologies
        for i in range(0, n):
            self.partitions.append(Topo())

        # Assign switches and hosts to partitions
        for node in self.topo.nodes():
            part = self.placer.place(node)
            self.nodeToPart[node] = part
            # Assign nodes to sub-topologies
            self.partitions[part].addNode(node,**self.topo.nodeInfo(node))

        # Add links
        for link in self.topo.links():
            if self.nodeToPart[link[0]] == self.nodeToPart[link[1]]:
                self.partitions[self.nodeToPart[link[0]]].addLink(link[0],link[1],**self.topo.linkInfo(link[0],link[1]))
            else:
                self.tunnels.append([link[0],link[1],self.topo.linkInfo(link[0],link[1])])            
            
        return Cluster(self.partitions,self.tunnels)


if __name__ == "__main__":
    lt = LinearTopo(20, 1)
    for l in lt.links():
        lt.setlinkInfo(l[0], l[1], {"bw":10, "delay":"1"})

    print 'Original Topology:\n', lt.nodes()
    for p in ['mn-random', 'mn-roundRobin', 'mn-switchBin', 'mn-hostSwitchBin']:
        mininetPart = MininetPartitioner(lt)
        subtopos = mininetPart.partition(4, p)
        print p, 'placer:', subtopos.getTopos()
        for item in subtopos.getTopos():
            print item.nodes()

