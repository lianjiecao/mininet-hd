import subprocess, os, logging, time
from mininet.topo import Topo

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
    Use metis with vertex and edge weight
    """

    def __init__(self,tool="~/Chaco-2.2/exec/chaco"):
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"
        self.toolCMD = tool

    def loadtopo(self,topo):
        i=1
        self.pos = {}
        self.switches = {}
        self.hostToSw = {}
        self.tunnels = []
        self.partitions = []
        self.topo = topo
        graphFile = [[]] # <-- index 0 is header
        # Replace the original name of nodes with integers starting from 0 and 
        # record the mapping between original name and new name for later recovering
        for switch in topo.switches():
            self.switches[switch] = i
            self.pos[i] = switch
            graphFile.append([i, 0])
            i+=1
        swLinks = 0
        for link in topo.links():
            # Links between switch and host
            # if(topo.isSwitch(link[0]) and not topo.isSwitch(link[1])):
            #     metis[self.switches[link[0]]][0]=metis[self.switches[link[0]]][0]+1
            # elif(topo.isSwitch(link[1]) and not topo.isSwitch(link[0])):
            #     metis[self.switches[link[1]]][0]=metis[self.switches[link[1]]][0]+1
            # Links between switches
            # else:
            if (topo.isSwitch(link[0]) and topo.isSwitch(link[1])): # Links between 2 switches
                graphFile[self.switches[link[0]]] += [self.switches[link[1]],int(topo.linkInfo(link[0],link[1])["bw"])]
                graphFile[self.switches[link[1]]] += [self.switches[link[0]],int(topo.linkInfo(link[0],link[1])["bw"])]
                graphFile[self.switches[link[0]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                graphFile[self.switches[link[1]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
            
#                graphFile[self.switches[link[1]]].append(self.switches[link[0]])
#                graphFile[self.switches[link[0]]].append(int(topo.linkInfo(link[0],link[1])["bw"]))
#                graphFile[self.switches[link[1]]].append(int(topo.linkInfo(link[0],link[1])["bw"]))
                swLinks += 1
            elif topo.isSwitch(link[0]):
                self.hostToSw[link[1]] = link[0]
            elif topo.isSwitch(link[1]):
                self.hostToSw[link[0]] = link[1]
#            if topo.isSwitch(link[0]):
#                metis[self.switches[link[0]]][0] = metis[self.switches[link[0]]][0] + int(topo.linkInfo(link[0],link[1])["bw"])
#            if topo.isSwitch(link[1]):
#                metis[self.switches[link[1]]][0] = metis[self.switches[link[1]]][0] + int(topo.linkInfo(link[0],link[1])["bw"])
            # else:
            #     metis[self.switches[link[0]]].append(100)
            #     metis[self.switches[link[1]]].append(100)
                
        #write header
        graphFile[0]=[len(self.switches), swLinks ,"111"]
        ret = ""
        for line in graphFile:
            ret = ret + " ".join(map(str,line)) + "\n"
        self.graph=self._write_to_file(ret)


    def _convert_to_plain_topo(self, topo):
        r = Topo()
        for node in topo.nodes():
            r.addNode(node,**topo.nodeInfo(node))
        for edge in topo.links():
            r.addLink(edge[0],edge[1],**topo.linkInfo(edge[0],edge[1]))
        return r

    def partition(self,n, alg="chaco", shares=None):
        self.tunnels=[]
        self.partitions=[]
        # Write Chaco input parameters
        inputPara = self.toolCMD+'.in'
        subprocess.call('echo "'+self.graph+'\n'+self.graph+'.out\n1\n50\n2\n2\nn\n" > '+inputPara, shell=True)
        subprocess.call('echo "'+self.chacoCtlPara+'" > User_Params', shell=True)
        
        if(n>1 and len(self.switches)>1):
            startT = time.time()
            outp=subprocess.check_output(["cat "+inputPara+" | "+self.toolCMD],shell=True)
            #print "Chaco-partition:", time.time()-startT
            self.logger.debug(outp)
            startT = time.time()
            self._parse_chaco_result(self.graph+".out",n)
            #print "Chaco-reconstruct:", time.time()-startT
            os.remove(self.graph+".out")
            os.remove(self.graph)
        else:
            tpart = [self._convert_to_plain_topo(self.topo)]
            while(len(tpart) < n):
                tpart.append(Topo())
            self.partitions = tpart
            
        return Clustering(self.partitions,self.tunnels)

        
    def _write_to_file(self,pstr):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            filename=os.tempnam()
        self.logger.debug("Chaco input file: "+filename)
        self.logger.debug(pstr)
        f = open(filename,"w")
        f.write(pstr)
        f.close()
        return filename
   
    def _parse_chaco_result(self,filepath,n):
        for i in range(0,n):
            self.partitions.append(Topo())
        f = open(filepath,"r")
        lnIdx = 1
        switch_to_part={}
        # Add switches from the output file
        for line in f:
            part = int(line)
            switch_to_part[self.pos[lnIdx]]=part
            self.partitions[part].addNode(self.pos[lnIdx],**self.topo.nodeInfo(self.pos[lnIdx]))
            lnIdx += 1
        f.close()
        startT = time.time()
        # Add hosts from the original topology
#        for node in self.topo.nodes():
#            if not self.topo.isSwitch(node):
#                for edge in self.topo.links():
#                    if(edge[0]==node):
#                        self.partitions[switch_to_part[edge[1]]].addNode(node,**self.topo.nodeInfo(node))
                        # print node, edge[0], edge[1], self.topo.linkInfo(node,edge[1])
#                        self.partitions[switch_to_part[edge[1]]].addLink(node,edge[1],**self.topo.linkInfo(node,edge[1]))
#                    if(edge[1]==node):
#                        self.partitions[switch_to_part[edge[0]]].addNode(node,**self.topo.nodeInfo(node))
#                        self.partitions[switch_to_part[edge[0]]].addLink(edge[0],node,**self.topo.linkInfo(edge[0],node))
        for hs in self.hostToSw:
            self.partitions[switch_to_part[self.hostToSw[hs]]].addNode(hs, **self.topo.nodeInfo(hs))
            self.partitions[switch_to_part[self.hostToSw[hs]]].addLink(hs, self.hostToSw[hs] , **self.topo.linkInfo(hs, self.hostToSw[hs]))


        #print "Chaco-addNodes:", time.time()-startT
        startT = time.time()
        
        # Recover links and record tunnels
        for edge in self.topo.links():
            if (self.topo.isSwitch(edge[0]) and self.topo.isSwitch(edge[1])):
                if(switch_to_part[edge[0]] == switch_to_part[edge[1]]):
                    self.partitions[switch_to_part[edge[0]]].addLink(edge[0],edge[1],**self.topo.linkInfo(edge[0],edge[1]))
                else:
                    self.tunnels.append([edge[0],edge[1],self.topo.linkInfo(edge[0],edge[1])])
        #print "Chaco-addLinks:", time.time()-startT
        self.logger.debug("Topologies:")
        for t in self.partitions:
            self.logger.debug("Partition "+str(self.partitions.index(t)))
            self.logger.debug("Nodes: "+str(t.nodes()))
            self.logger.debug("Links: "+str(t.links()))
        self.logger.debug("Tunnels: "+str(self.tunnels))

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
