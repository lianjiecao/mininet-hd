import subprocess, os, logging, sys, copy
from mininet.topo import Topo

# the following block is to support deprecation warnings. this is really not
# solved nicely and should probably be somewhere else
import warnings
import functools
EasyScale_path = os.path.abspath('/home/maxinet/EasyScale-MaxiNet')
sys.path.insert(0, EasyScale_path)
import inputParser

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
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
    Use metis with edge weight
    """

    tmpES = "/tmp/EasyScale/"
    os.system("mkdir " + tmpES + " 2>/dev/null")
    esPath = "/home/maxinet/EasyScale-MaxiNet/run_easyscale.sh"
    tcl_file = tmpES + "vtopDeter.tcl"
    node_file = tmpES + "vtopNode.txt"
    vtop_file = tmpES + "vtop.xml"
    hardware_file = "/home/maxinet/EasyScale-MaxiNet/hardware.xml"
    map_file = tmpES + "esOut.xml"

    def __init__(self,metis="gpmetis -ptype=rb"):
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.metisCMD = metis


    def loadtopo(self, topo):
        self.topo = topo
        # if (alg is "metis"):
        #     i=1
        #     self.pos={}
        #     self.switches={}
        #     self.tunnels=[]
        #     self.partitions=[]
        #     metis=[[]] # <-- index 0 is header
        #     for switch in topo.switches():
        #         self.switches[switch]=i
        #         self.pos[i]=switch
        #         i+=1
        #         metis.append([])

        #     links=0
        #     for link in topo.links():
        #         # # Links between switch and host
        #         # if(topo.isSwitch(link[0]) and not topo.isSwitch(link[1])):
        #         #     metis[self.switches[link[0]]][0]=metis[self.switches[link[0]]][0]+1
        #         # elif(topo.isSwitch(link[1]) and not topo.isSwitch(link[0])):
        #         #     metis[self.switches[link[1]]][0]=metis[self.switches[link[1]]][0]+1
        #         # # Links between switches
        #         # else:
        #         if (topo.isSwitch(link[0]) and topo.isSwitch(link[1])):
        #             metis[self.switches[link[0]]].append(self.switches[link[1]])
        #             metis[self.switches[link[1]]].append(self.switches[link[0]])
        #             if(topo.linkInfo(link[0],link[1]).has_key("bw")):
        #                 metis[self.switches[link[0]]].append(int(topo.linkInfo(link[0],link[1])["bw"]))
        #                 metis[self.switches[link[1]]].append(int(topo.linkInfo(link[0],link[1])["bw"]))
        #             else:
        #                 metis[self.switches[link[0]]].append(100)
        #                 metis[self.switches[link[1]]].append(100)
        #             links+=1

        #     #write header
        #     metis[0]=[len(self.switches),links,"001 0"]
        #     ret = ""
        #     for line in metis:
        #         ret = ret + " ".join(map(str,line)) + "\n"
        #     self.graph=self._write_to_file(ret)
        # else:
        # Dump mininet topology object to tcl file
        '''
        1. Convert Mininet topology object to tcl format for EasyScale
        2. Generate virtual node resource resouce file 
        3. Generate hardware description file
        '''

        tcl_header = "set ns [new Simulator]" + "\n" + "source tb_compat.tcl" + "\n"
        tcl_nodes = "### Nodes" + "\n"
        tcl_links = "### Links" + "\n"

        node_header = "#For automap & EasyScale (backward compatible): " + "\n" \
            "#NSname VclassID FidelityIndex nodeType (resource,value,type)|(resource,value)" + "\n" \
            "# NSname, VclassID, FidelityIndex, nodeType are REQUIRED" + "\n\n" \
            "# pc type will be taken care of first" + "\n" \
            "#For EasyScale: (for individual vnode)" + "\n" \
            "#Type of virtualization technique:" + "\n" \
            "#   (containers:node_type,embedded_pnode)" + "\n" \
            "#   (containers:node_type,qemu)" + "\n" \
            "#   (containers:node_type,openvz) #Default" + "\n" \
            "#   (containers:node_type,process)"  + "\n"
        node_nodes = ""
        for node in topo.nodes():
            if topo.isSwitch(node):
                tcl_nodes = tcl_nodes + "set " + str(node) + " [$ns switch]" + "\n"
            else:
                tcl_nodes = tcl_nodes + "set " + str(node) + " [$ns host]" + "\n"
            node_nodes = node_nodes + str(node) + " 0 1 pc1 (containers:node_type,openvz)" + "\n"

        # print tcl_nodes

        for i, link in enumerate(topo.links(sort = True)):
            src = link[0]
            dst = link[1]
            #get their opts:
            # key = tuple(sorted([src, dst]))
            li_info = topo.linkInfo(link[0], link[1])
            # print li_info
            tcl_links = tcl_links + "set link" + str(i) + " [$ns duplex-link $" + str(src) + " $" + str(dst)+ " " + \
                str(li_info["bw"]) + "Mb " + li_info["delay"] + " DropTail]\n"
            i = i + 1
        # print tcl_links

        ending = "$ns rtproto Static" + "\n" + "$ns run"
        tcl_f = open(self.tcl_file, "w")
        tcl_f.write(tcl_header + "\n" + tcl_nodes + "\n" + tcl_links + "\n" + ending + "\n")
        tcl_f.close()

        node_f = open(self.node_file, "w")
        node_f.write(node_header + "\n" + node_nodes + "\n")
        node_f.close()


    def _convert_to_plain_topo(self, topo):
        r = Topo()
        for node in topo.nodes():
            r.addNode(node,**topo.nodeInfo(node))
        for edge in topo.links():
            r.addLink(edge[0],edge[1],**topo.linkInfo(edge[0],edge[1]))
        return r

    def partition(self, n, shares=None):

        # if (alg is "metis"):
        #     self.tunnels=[]
        #     self.partitions=[]
        #     if(n>1 and len(self.switches)>1):
        #         if(shares):
        #             tpw=""
        #             for i in range(0,n):
        #                 tpw+=str(i)+ " = " +str(shares[i])+"\n"
        #             tpwf=self._write_to_file(tpw)
        #             outp=subprocess.check_output([self.metisCMD+" -tpwgts="+tpwf+" "+self.graph+" "+str(n)],shell=True)
        #             os.remove(tpwf)
        #         else:
        #             outp=subprocess.check_output([self.metisCMD+" "+self.graph+" "+str(n)],shell=True)
        #         self.logger.debug(outp)
        #         self._parse_metis_result(self.graph+".part."+str(n),n)
        #         os.remove(self.graph+".part."+str(n))
        #         os.remove(self.graph)
        #     else:
        #         tpart = [self._convert_to_plain_topo(self.topo)]
        #         while(len(tpart) < n):
        #             tpart.append(Topo())
        #         self.partitions = tpart
                
        #     return Clustering(self.partitions,self.tunnels)
        # else:
        os.system("bash " + self.esPath + " " + self.tcl_file + " " + self.node_file + \
        " " + self.vtop_file + " " +self.hardware_file + " " + self.map_file)

        self.readEasyScaleFile(n)
        return Clustering(self.topoWname.values(),self.tunnelsWname)


    def readEasyScaleFile(self, numWorkers):
        self.logger.debug("Reading EasyScale results ...")
        vtop = inputParser.parseVTopology(self.map_file, True)
        # Create Topo object for each worker (PC) 

        self.topoWname = {}
        self.tunnelsWname = list()
        # origLinks = copy.deepcopy(self.topo.links())
        origLinks = self.topo.links()
        self.logger.debug("Original Links = " + str(origLinks))
        for w in vtop.nodes:
            self.topoWname[w["name"]] = Topo()
            if w["mapping"] is not None:
                # Add mapped hosts and switches to the Topo object 
                self.logger.debug(w["name"] + " Topo object:")
                for nodeName in [x["name"] for x in w["mapping"].nodes]:
                    if self.topo.isSwitch(nodeName):
                        # build a new switch that is exactly like node
                        # and put it into topo part ( topoWname[part] )
                        n = copy.deepcopy(self.topo.nodeInfo(nodeName))
                        self.logger.debug( "\t" + nodeName + " " + str(n))
                        n.pop('isSwitch', None)
                        self.topoWname[w["name"]].addSwitch(nodeName, **n)
                    else :
                        n = self.topo.nodeInfo(nodeName)
                        self.topoWname[w["name"]].addHost(nodeName, **n)
                # Add links to the Topo object 
                for linkEnds in [(x["ends"][0], x["ends"][1]) for x in w["mapping"].links]:
                    # print linkEnds
                    if linkEnds not in self.topo.links(): # Handle disordered end pair
                        linkEnds = (linkEnds[1], linkEnds[0])
                    l = self.topo.link_info[linkEnds]
                    self.logger.debug("\t" + str(linkEnds) +" "+ str(l))
                    self.topoWname[w["name"]].addLink(linkEnds[0], linkEnds[1], **l)
                    origLinks.remove(linkEnds)
        # Creat tunnels between workers
        self.logger.debug("Remaining links = " + str(origLinks))
        # print "Tunnels:"
        for linkEnds in origLinks:
            srcTopo = ""
            dstTopo = ""
            for w in vtop.nodes:
                if linkEnds[0] in w["mapping"]:
                    srcTopo = w["name"]
                if linkEnds[1] in w["mapping"]:
                    dstTopo = w["name"]
            # print srcTopo, dstTopo
            if srcTopo is not dstTopo:
                l = self.topo.link_info[linkEnds]
                self.tunnelsWname.append([linkEnds[0], linkEnds[1], \
                    {"bw":float(l["bw"]), "delay":l["delay"]}])
                # print "\t", linkEnds[0], "=>", linkEnds[1]
        del origLinks[:]

        
    def _write_to_file(self,pstr):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            filename=os.tempnam()
        self.logger.debug("metis file: "+filename)
        self.logger.debug(pstr)
        f = open(filename,"w")
        f.write(pstr)
        f.close()
        return filename
    
    def _parse_metis_result(self,filepath,n):
        for i in range(0,n):
            self.partitions.append(Topo())
        f = open(filepath,"r")
        i = 1
        switch_to_part={}
        for line in f:
            part = int(line)
            switch_to_part[self.pos[i]]=part
            self.partitions[part].addNode(self.pos[i],**self.topo.nodeInfo(self.pos[i]))
            i=i+1
        f.close()
        for node in self.topo.nodes():
            if not self.topo.isSwitch(node):
                for edge in self.topo.links():
                    if(edge[0]==node):
                        self.partitions[switch_to_part[edge[1]]].addNode(node,**self.topo.nodeInfo(node))
                        # print node, edge[0], edge[1], self.topo.linkInfo(node,edge[1])
                        self.partitions[switch_to_part[edge[1]]].addLink(node,edge[1],**self.topo.linkInfo(node,edge[1]))
                    if(edge[1]==node):
                        self.partitions[switch_to_part[edge[0]]].addNode(node,**self.topo.nodeInfo(node))
                        self.partitions[switch_to_part[edge[0]]].addLink(edge[0],node,**self.topo.linkInfo(edge[0],node))
        for edge in self.topo.links():
            if (self.topo.isSwitch(edge[0]) and self.topo.isSwitch(edge[1])):
                if(switch_to_part[edge[0]] == switch_to_part[edge[1]]):
                    self.partitions[switch_to_part[edge[0]]].addLink(edge[0],edge[1],**self.topo.linkInfo(edge[0],edge[1]))
                else:
                    self.tunnels.append([edge[0],edge[1],self.topo.linkInfo(edge[0],edge[1])])
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
