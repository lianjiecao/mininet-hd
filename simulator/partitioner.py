import subprocess, os, logging, time
from mininet.log import setLogLevel, debug, info, error
from mininet.topo import Topo, LinearTopo
from random import randrange
from cluster import Placer, RoundRobinPlacer, RandomPlacer, SwitchBinPlacer, HostSwitchBinPlacer
# the following block is to support deprecation warnings. this is really not
# solved nicely and should probably be somewhere else
import warnings
import functools

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logging.basicConfig()


# class Placer( object ):
#     "Node placement algorithm for MininetCluster"
    
#     def __init__( self, servers=None, nodes=None, hosts=None,
#               switches=None, controllers=None, links=None ):
#         """Initialize placement object
#         servers: list of servers
#         nodes: list of all nodes
#         hosts: list of hosts
#         switches: list of switches
#         controllers: list of controllers
#         links: list of links
#         (all arguments are optional)
#         returns: server"""
#         self.servers = servers or []
#         self.nodes = nodes or []
#         self.hosts = hosts or []
#         self.switches = switches or []
#         self.controllers = controllers or []
#         self.links = links or []

#     def place( self, node ):
#         "Return server for a given node"
#         assert self, node  # satisfy pylint
#         # Default placement: run locally
#         return 'localhost'


# class RandomPlacer( Placer ):
#     "Random placement"
#     def place(self, nodename):
#         """Random placement function
#             nodename: node name"""
#         assert nodename  # please pylint
#         # This may be slow with lots of servers
#         return self.servers[randrange(0, len(self.servers))]


# class RoundRobinPlacer( Placer ):
#     """Round-robin placement
#        Note this will usually result in cross-server links between
#        hosts and switches"""

#     def __init__( self, *args, **kwargs ):
#         Placer.__init__( self, *args, **kwargs )
#         self.next = 0

#     def place(self, nodename):
#         """Round-robin placement function
#             nodename: node name"""
#         assert nodename  # please pylint
#         # This may be slow with lots of servers
#         server = self.servers[self.next]
#         self.next = (self.next + 1) % len(self.servers)
#         return server


# class SwitchBinPlacer( Placer ):
#     """Place switches (and controllers) into evenly-sized bins,
#        and attempt to co-locate hosts and switches"""

#     def __init__( self, *args, **kwargs ):
#         Placer.__init__( self, *args, **kwargs )
#         # Easy lookup for servers and node sets
#         self.servdict = dict( enumerate( self.servers ) )
#         self.hset = frozenset( self.hosts )
#         self.sset = frozenset( self.switches )
#         self.cset = frozenset( self.controllers )
#         # Server and switch placement indices
#         self.placement = self.calculatePlacement()

#     @staticmethod
#     def bin( nodes, servers ):
#         "Distribute nodes evenly over servers"
#         # Calculate base bin size
#         nlen = len( nodes )
#         slen = len( servers )
#         # Basic bin size
#         quotient = int( nlen / slen )
#         binsizes = { server: quotient for server in servers }
#         # Distribute remainder
#         remainder = nlen % slen
#         for server in servers[ 0 : remainder ]:
#             binsizes[ server ] += 1
#         # Create binsize[ server ] tickets for each server
#         tickets = sum( [ binsizes[ server ] * [ server ]
#                          for server in servers ], [] )
#         # And assign one ticket to each node
#         return { node: ticket for node, ticket in zip( nodes, tickets ) }

#     def calculatePlacement( self ):
#         "Pre-calculate node placement"
#         placement = {}
#         # Create host-switch connectivity map,
#         # associating host with last switch that it's
#         # connected to
#         switchFor = {}
#         for src, dst in self.links:
#             if src in self.hset and dst in self.sset:
#                 switchFor[ src ] = dst
#             if dst in self.hset and src in self.sset:
#                 switchFor[ dst ] = src
#         # Place switches
#         placement = self.bin( self.switches, self.servers )
#         # Place controllers and merge into placement dict
#         placement.update( self.bin( self.controllers, self.servers ) )
#         # Co-locate hosts with their switches
#         for h in self.hosts:
#             if h in placement:
#                 # Host is already placed - leave it there
#                 continue
#             if h in switchFor:
#                 placement[ h ] = placement[ switchFor[ h ] ]
#             else:
#                 raise Exception(
#                         "SwitchBinPlacer: cannot place isolated host " + h )
#         return placement

#     def place( self, node ):
#         """Simple placement algorithm:
#            place switches into evenly sized bins,
#            and place hosts near their switches"""
#         return self.placement[ node ]


# class HostSwitchBinPlacer( Placer ):
#     """Place switches *and hosts* into evenly-sized bins
#        Note that this will usually result in cross-server
#        links between hosts and switches"""

#     def __init__( self, *args, **kwargs ):
#         Placer.__init__( self, *args, **kwargs )
#         # Calculate bin sizes
#         scount = len( self.servers )
#         self.hbin = max( int( len( self.hosts ) / scount ), 1 )
#         self.sbin = max( int( len( self.switches ) / scount ), 1 )
#         self.cbin = max( int( len( self.controllers ) / scount ), 1 )
#         info( 'scount:', scount )
#         info( 'bins:', self.hbin, self.sbin, self.cbin, '\n' )
#         self.servdict = dict( enumerate( self.servers ) )
#         self.hset = frozenset( self.hosts )
#         self.sset = frozenset( self.switches )
#         self.cset = frozenset( self.controllers )
#         self.hind, self.sind, self.cind = 0, 0, 0

#     def place( self, nodename ):
#         """Simple placement algorithm:
#             place nodes into evenly sized bins"""
#         # Place nodes into bins
#         if nodename in self.hset:
#             server = self.servdict[ self.hind / self.hbin ]
#             self.hind += 1
#         elif nodename in self.sset:
#             server = self.servdict[ self.sind / self.sbin ]
#             self.sind += 1
#         elif nodename in self.cset:
#             server = self.servdict[ self.cind / self.cbin ]
#             self.cind += 1
#         else:
#             info( 'warning: unknown node', nodename )
#             server = self.servdict[ 0 ]
#         return server

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

    def __init__(self, topo, tool):

        """
        Initialize all data structures that may be used in the partitioning process.
        """
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"
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
                self.graphFile[self.switches[link[0]]] += [self.switches[link[1]],int(topo.linkInfo(link[0],link[1])["bw"])]
                self.graphFile[self.switches[link[1]]] += [self.switches[link[0]],int(topo.linkInfo(link[0],link[1])["bw"])]
                self.graphFile[self.switches[link[0]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.graphFile[self.switches[link[1]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.swLinks += 1
            elif topo.isSwitch(link[0]):
                self.hostToSw[link[1]] = link[0]
                # self.swToHost.setdefault(link[0], []).append(link[1])
            elif topo.isSwitch(link[1]):
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
    def __init__(self, topo, tool):
        Placer.__init__( self, topo, tool="gpmetis -ptype=rb")


    def partition(self, n, alg="metis", shares=None):

        # Create input file for METIS, removing the first swName
        self.graphFile[0]=[len(self.switches), self.swLinks, "011 0"]
        self.graphFile = [x[1:] for x in self.graphFile]

        self.graph = self._write_to_file()

        if n > 1 and len(self.switches) > 1:
            if(shares):
                tpw=""
                for i in range(0, n):
                    tpw += str(i) + " = " + str(shares[i]) + "\n"
                tpwf = self._write_to_file(tpw)
                outp = subprocess.check_output([self.toolCMD + " -tpwgts=" + tpwf + " " + self.graph + " " + str(n)], shell=True)
                os.remove(tpwf)
            else:
                startT = time.time()
                outp = subprocess.check_output([self.toolCMD + " " + self.graph + " " + str(n)], shell=True)
                # print "Metis-partition:", time.time()-startT
            self.logger.debug(outp)
            
            startT = time.time()
            self._parse_tool_result(self.graph + ".part." + str(n), n)
            #print "Metis-reconstruct:", time.time()-startT
            os.remove(self.graph + ".part." + str(n))
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Clustering(self.partitions,self.tunnels)


    def _write_to_file(self, graph):
        """
        Dump the graph to a file for graph partition tools
        """
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line[1:])) + "\n"

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
            self.nodeToPart[self.pos[i]] = part
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
                    self.partitions[self.nodeToPart[edge[0]]].addLink(edge[0],edge[1],**self.topo.linkInfo(edge[0],edge[1]))
                else:
                    self.tunnels.append([edge[0],edge[1],self.topo.linkInfo(edge[0],edge[1])])
        #print "Metis-addLinks:", time.time()-startT
        self.logger.debug("Topologies:")
        for t in self.partitions:
            self.logger.debug("Partition "+str(self.partitions.index(t)))
            self.logger.debug("Nodes: "+str(t.nodes()))
            self.logger.debug("Links: "+str(t.links()))
        self.logger.debug("Tunnels: "+str(self.tunnels))


class ChacoPartitioner(MetisPartitioner):
    """
    Chaco partitioner with multilevel KL
    """

    def __init__(self, topo, tool): 
        Placer.__init__( self, topo, tool='~/Chaco-2.2/exec/chaco')
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"
        self.toolCMD = tool

    def partition(self, n, alg="chaco", shares=None):
        graphFile[0] = [len(self.switches), swLinks ,"111"]
        self.graph = self._write_to_file()

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
            
        return Clustering(self.partitions,self.tunnels)


class MininetPartitioner(Partitioner):
    """
    Wrapper of Mininet placers
    """
    def __init__(self, topo, tool): 
        Placer.__init__( self, topo)
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
            
        return Clustering(self.partitions,self.tunnels)


if __name__ == "__main__":
    lt = LinearTopo(20, 1)
    print 'Original Topology:\n', lt.nodes()
    mininetPart = Partitioner(lt)
    for p in ['mn-random', 'mn-roundRobin', 'mn-switchBin', 'mn-hostSwitchBin']:
        subtopos = mininetPart.partition(4, p)
        print p, 'placer:'
        for item in subtopos.getTopos():
            print item.nodes()