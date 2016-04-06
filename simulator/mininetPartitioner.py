import subprocess, os, logging, time
from mininet.log import setLogLevel, debug, info, error
from mininet.topo import Topo, LinearTopo
from random import randrange
# the following block is to support deprecation warnings. this is really not
# solved nicely and should probably be somewhere else
import warnings
import functools

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logging.basicConfig()

def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        logger.warn("Call to deprecated function {}.".format(func.__name__))
        warnings.warn_explicit(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)
    return new_func

class Placer( object ):
    "Node placement algorithm for MininetCluster"
    
    def __init__( self, servers=None, nodes=None, hosts=None,
              switches=None, controllers=None, links=None ):
        """Initialize placement object
        servers: list of servers
        nodes: list of all nodes
        hosts: list of hosts
        switches: list of switches
        controllers: list of controllers
        links: list of links
        (all arguments are optional)
        returns: server"""
        self.servers = servers or []
        self.nodes = nodes or []
        self.hosts = hosts or []
        self.switches = switches or []
        self.controllers = controllers or []
        self.links = links or []

    def place( self, node ):
        "Return server for a given node"
        assert self, node  # satisfy pylint
        # Default placement: run locally
        return 'localhost'


class RandomPlacer( Placer ):
    "Random placement"
    def place(self, nodename):
        """Random placement function
            nodename: node name"""
        assert nodename  # please pylint
        # This may be slow with lots of servers
        return self.servers[randrange(0, len(self.servers))]


class RoundRobinPlacer( Placer ):
    """Round-robin placement
       Note this will usually result in cross-server links between
       hosts and switches"""

    def __init__( self, *args, **kwargs ):
        Placer.__init__( self, *args, **kwargs )
        self.next = 0

    def place(self, nodename):
        """Round-robin placement function
            nodename: node name"""
        assert nodename  # please pylint
        # This may be slow with lots of servers
        server = self.servers[self.next]
        self.next = (self.next + 1) % len(self.servers)
        return server


class SwitchBinPlacer( Placer ):
    """Place switches (and controllers) into evenly-sized bins,
       and attempt to co-locate hosts and switches"""

    def __init__( self, *args, **kwargs ):
        Placer.__init__( self, *args, **kwargs )
        # Easy lookup for servers and node sets
        self.servdict = dict( enumerate( self.servers ) )
        self.hset = frozenset( self.hosts )
        self.sset = frozenset( self.switches )
        self.cset = frozenset( self.controllers )
        # Server and switch placement indices
        self.placement = self.calculatePlacement()

    @staticmethod
    def bin( nodes, servers ):
        "Distribute nodes evenly over servers"
        # Calculate base bin size
        nlen = len( nodes )
        slen = len( servers )
        # Basic bin size
        quotient = int( nlen / slen )
        binsizes = { server: quotient for server in servers }
        # Distribute remainder
        remainder = nlen % slen
        for server in servers[ 0 : remainder ]:
            binsizes[ server ] += 1
        # Create binsize[ server ] tickets for each server
        tickets = sum( [ binsizes[ server ] * [ server ]
                         for server in servers ], [] )
        # And assign one ticket to each node
        return { node: ticket for node, ticket in zip( nodes, tickets ) }

    def calculatePlacement( self ):
        "Pre-calculate node placement"
        placement = {}
        # Create host-switch connectivity map,
        # associating host with last switch that it's
        # connected to
        switchFor = {}
        for src, dst in self.links:
            if src in self.hset and dst in self.sset:
                switchFor[ src ] = dst
            if dst in self.hset and src in self.sset:
                switchFor[ dst ] = src
        # Place switches
        placement = self.bin( self.switches, self.servers )
        # Place controllers and merge into placement dict
        placement.update( self.bin( self.controllers, self.servers ) )
        # Co-locate hosts with their switches
        for h in self.hosts:
            if h in placement:
                # Host is already placed - leave it there
                continue
            if h in switchFor:
                placement[ h ] = placement[ switchFor[ h ] ]
            else:
                raise Exception(
                        "SwitchBinPlacer: cannot place isolated host " + h )
        return placement

    def place( self, node ):
        """Simple placement algorithm:
           place switches into evenly sized bins,
           and place hosts near their switches"""
        return self.placement[ node ]


class HostSwitchBinPlacer( Placer ):
    """Place switches *and hosts* into evenly-sized bins
       Note that this will usually result in cross-server
       links between hosts and switches"""

    def __init__( self, *args, **kwargs ):
        Placer.__init__( self, *args, **kwargs )
        # Calculate bin sizes
        scount = len( self.servers )
        self.hbin = max( int( len( self.hosts ) / scount ), 1 )
        self.sbin = max( int( len( self.switches ) / scount ), 1 )
        self.cbin = max( int( len( self.controllers ) / scount ), 1 )
        info( 'scount:', scount )
        info( 'bins:', self.hbin, self.sbin, self.cbin, '\n' )
        self.servdict = dict( enumerate( self.servers ) )
        self.hset = frozenset( self.hosts )
        self.sset = frozenset( self.switches )
        self.cset = frozenset( self.controllers )
        self.hind, self.sind, self.cind = 0, 0, 0

    def place( self, nodename ):
        """Simple placement algorithm:
            place nodes into evenly sized bins"""
        # Place nodes into bins
        if nodename in self.hset:
            server = self.servdict[ self.hind / self.hbin ]
            self.hind += 1
        elif nodename in self.sset:
            server = self.servdict[ self.sind / self.sbin ]
            self.sind += 1
        elif nodename in self.cset:
            server = self.servdict[ self.cind / self.cbin ]
            self.cind += 1
        else:
            info( 'warning: unknown node', nodename )
            server = self.servdict[ 0 ]
        return server


class Clustering:
    def __init__(self,topologies, tunnels):
        self.topos = topologies
        self.tunnels = tunnels
    
    def getTunnels(self):
        return self.tunnels

    def getTopos(self):
        return self.topos

class Partitioner:
    """
    Use graph with vertex and edge weight
    """

    def __init__(self, tool="~/KaHIPv0.73/deploy/kaffpa"):
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.toolCMD = tool
        self.placers = {'mn-random': RandomPlacer, 'mn-roundRobin': RoundRobinPlacer,
            'mn-switchBin':SwitchBinPlacer, 'mn-hostSwitchBin':HostSwitchBinPlacer}

    def loadtopo(self, topo):
        i = 1
        self.pos = {}
        self.switches = {}
        self.hostToSw = {}
        self.swToHost = {}
        self.swToPart={}
        self.nodeToPart = {}
        self.tunnels = []
        self.partitions = []
        self.topo = topo
        graphFile = [[]] # <-- index 0 is header

        # Never used
        for link in self.topo.links():
            if self.topo.isSwitch(link[0]) and not self.topo.isSwitch(link[1]):
                self.swToHost.setdefault(link[0], []).append(link[1])
            if self.topo.isSwitch(link[1]) and not self.topo.isSwitch(link[0]):
                self.swToHost.setdefault(link[1], []).append(link[0])

    def partition(self, n, alg='mn-random', shares=None):

        self.alg = alg
        self.placer = self.placers[self.alg](servers=[x for x in range(4)], nodes=self.topo.nodes(), 
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


class partitioner:

    @deprecated
    def __init__(self,string):
        self.partitioner = Partitioner()

    @deprecated
    def clusterTopology(self,topo,n):
        self.partitioner.loadtopo(topo)
        self.clustering = self.partitioner.partition(n)

    @deprecated
    def getTunnels(self):
        return self.partitioner.getTunnels()

    @deprecated
    def getTopos(self):
        return self.partitioner.getTopos()     


if __name__ == "__main__":
    lt = LinearTopo(20, 1)
    print 'Original Topology:\n', lt.nodes()
    mininetPart = Partitioner()
    for p in ['mn-random', 'mn-roundRobin', 'mn-switchBin', 'mn-hostSwitchBin']:
        mininetPart.loadtopo(lt)
        subtopos = mininetPart.partition(4, p)
        print p, 'placer:'
        for item in subtopos.getTopos():
            print item.nodes()

