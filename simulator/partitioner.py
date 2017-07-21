import subprocess, os, logging, time, warnings, sys, functools, uuid, shutil
from mininet.log import setLogLevel, debug, info, error
from mininet.topo import Topo, LinearTopo
from cluster import Placer, RoundRobinPlacer, RandomPlacer, SwitchBinPlacer, HostSwitchBinPlacer
from math import ceil, log
from random import randrange
import numpy as np

import simulatorFunc
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
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
        self.swHostCPU = [[]]
        i = 1
        # Replace the original name of nodes with integers starting from 0 and 
        # record the mapping between original name and new name for later recovering
        for switch in topo.switches():
            self.switches[switch] = i
            self.pos[i] = switch
            self.graphFile.append([i, 0])
            self.swHostCPU.append([i, 0])
            i += 1
        self.swLinks = 0
        for link in topo.links():
        
            # For sw-sw links, store info in the format of [swName swWeight neighborSw_i edgeWeigth_i]
            # For host-sw links, store info for recovering subtopologies after partitioning
            if (topo.isSwitch(link[0]) and topo.isSwitch(link[1])): # Links between 2 switches
#                print 'sw-sw', link
                # Add neighbors
                self.graphFile[self.switches[link[0]]] += [self.switches[link[1]],int(topo.linkInfo(link[0],link[1])["bw"])]
                self.graphFile[self.switches[link[1]]] += [self.switches[link[0]],int(topo.linkInfo(link[0],link[1])["bw"])]
                # Update vertex weight
                self.graphFile[self.switches[link[0]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.graphFile[self.switches[link[1]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.swLinks += 1
            elif topo.isSwitch(link[0]):
#                print 'sw-ht', link
                self.graphFile[self.switches[link[0]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.hostToSw[link[1]] = link[0]
                if topo.nodeInfo(link[1]).get('cpu'):
                    self.swHostCPU[self.switches[link[0]]][1] += int(topo.nodeInfo(link[1]).get('cpu') * 100)
                # self.swToHost.setdefault(link[0], []).append(link[1])
            elif topo.isSwitch(link[1]):
#                print 'ht-sw', link
                self.graphFile[self.switches[link[1]]][1] += int(topo.linkInfo(link[0],link[1])["bw"])
                self.hostToSw[link[0]] = link[1]
                if topo.nodeInfo(link[0]).get('cpu'):
                    self.swHostCPU[self.switches[link[1]]][1] += int(topo.nodeInfo(link[0]).get('cpu') * 100)
                # self.swToHost.setdefault(link[1], []).append(link[0])

    def partition(self, n, alg="chaco", capFs=None):
        """
        This function needs to be overwritten for each specific partitioning algorithm
        """
        return Cluster(self.topo, self.tunnels)


    def dumpGraph(self, fName):

        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self._write_to_file('%s.graph' % fName, pstr)

        ### Create host CPU usage file
        hostCPUstr = ''
        for s in self.swHostCPU[1:]:
            hostCPUstr = hostCPUstr + '%d\n' % s[1]
        self.hostFile = self._write_to_file('%s.host' % fName, hostCPUstr)

        # inputPara = '%s-%s.in' % (self.toolCMD, fName)
        # dim = int(ceil(log(n, 2)))
        # caps = '\n'.join(map(str, shares+[0]*(2**dim-n)))
        # for f in shares:
        #     f[1].reverse()
        # capFs = '\n'.join(' '.join(map(str, [int(y*10000) for y in x[1]])) for x \
        #     in shares+[(None, [0]*len(shares[0][1]))]*(2**dim-n))

        # subprocess.call('echo "'+self.graph+'\n'+self.hostFile+'\n'+self.graph+'.out\n1\n50\n'\
        #     +str(dim)+'\n'+capFs+'\n2\nn\n" > '+inputPara, shell=True)
        # subprocess.call('cp %s %s.graph' % (self.graph, fName), shell=True)
        # subprocess.call('cp %s %s.host' % (self.hostFile, fName), shell=True)


    def _write_to_file(self, filename, pstr):
        """
        Dump the graph to a file for graph partition tools
        """
        # pstr = ""
        # for line in self.graphFile:
        #     pstr = pstr + " ".join(map(str, line)) + "\n"

        # with warnings.catch_warnings():
        #     warnings.simplefilter("ignore")
        #     filename = os.tempnam()
        self.logger.debug("Output file: " + filename)
        self.logger.debug(pstr)
        f = open(filename, "w")
        f.write(pstr)
        f.close()
        # return filename


    def genFilename(self):
        '''
        Generate a uuid filename in /tmp
        '''
        return '/tmp/%s' % uuid.uuid4()


class MetisPartitioner(Partitioner):
    """
    METIS Partitioner
    """
    def __init__(self, topo, tool=""):
        Partitioner.__init__( self, topo, tool="gpmetis -ptype=rb")


    def partition(self, alg="metis", capFs=None, pmInfo=None):

        # Create input file for METIS, removing the first swName
        self.graphFile = [x[1:] for x in self.graphFile]
        self.graphFile[0] = [len(self.switches), self.swLinks, "011 0"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)

        if capFs:
            print pmInfo
            print capFs
            ps = {x[0]:np.poly1d(x[1]) for x in capFs}
            maxCaps = [(capFs[i][0], int(ps[capFs[i][0]](pmInfo[i][1][2]))) for i in range(len(capFs))]
            print maxCaps
            topoW = simulatorFunc.checkTopo(self.topo)
            newCaps = simulatorFunc.adjustCap(topoW, maxCaps)
            selectedPMs = simulatorFunc.selectPMs(topoW, newCaps)
            n = len(selectedPMs)
                
        if n > 1 and len(self.switches) > 1:
            if capFs:
                metisShares = simulatorFunc.calcMetisShare(self.topo, [x[1] for x in selectedPMs])
                print metisShares

                tpw=""
                for i in range(n):
                    tpw += str(i) + " = " + str(metisShares[i]) + "\n"
                print tpw
                tpwf = self.genFilename()
                self._write_to_file(tpwf, tpw)
                cmd = '%s -tpwgts=%s %s %d' % (self.toolCMD, tpwf, self.graph, n)
                self.logger.debug(cmd)
                outp = subprocess.check_output(cmd, shell=True)
                os.remove(tpwf)
            else:
                startT = time.time()
                cmd = '%s %s %d' % (self.toolCMD, self.graph, str(n))
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
            self.partitions[self.nodeToPart[self.hostToSw[hs]]].addLink(**self.topo.linkInfo(hs, self.hostToSw[hs]))
            # self.partitions[self.nodeToPart[self.hostToSw[hs]]].addLink(hs, self.hostToSw[hs] , **self.topo.linkInfo(hs, self.hostToSw[hs]))

        #print "Metis-addNodes:", time.time()-startT
        startT = time.time()

        # Recover links and record tunnels
        for edge in self.topo.links():
            if (self.topo.isSwitch(edge[0]) and self.topo.isSwitch(edge[1])):
                if(self.nodeToPart[edge[0]] == self.nodeToPart[edge[1]]):
                    #print edge[0], edge[1], self.topo.linkInfo(edge[0],edge[1])
                    # self.partitions[self.nodeToPart[edge[0]]].addLink(edge[0], edge[1], **self.topo.linkInfo(edge[0],edge[1]))
                    self.partitions[self.nodeToPart[edge[0]]].addLink(**self.topo.linkInfo(edge[0],edge[1]))
                else:
                    self.tunnels.append([edge[0],edge[1], self.topo.linkInfo(edge[0], edge[1])])
        #print "Metis-addLinks:", time.time()-startT
        self.logger.debug('Topologies:')
        for t in self.partitions:
            self.logger.debug('Partition ' + str(self.partitions.index(t)))
            self.logger.debug('Nodes: ' + str(t.nodes()))
            self.logger.debug('Links: ' + str(t.links()))
        self.logger.debug('Tunnels: ' + str(self.tunnels))


class C90Partitioner(MetisPartitioner):
    """
    C90 using share-based METIS Partitioner
    """
    def __init__(self, topo, tool=""):
        Partitioner.__init__( self, topo, tool="gpmetis -ptype=rb")

    def partition(self, alg="c90", capFs=None, pmInfo=None):

        # Create input file for METIS, removing the first swName
        self.graphFile = [x[1:] for x in self.graphFile]
        self.graphFile[0] = [len(self.switches), self.swLinks, "011 0"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)

        if capFs:
            print pmInfo
            print capFs
            n = len(pmInfo)
        else:
            n = 1
                
        if n > 1 and len(self.switches) > 1:
            if capFs:
                coefs = [list(reversed(x)) for x in capFs]
                pmCapFs = [np.poly1d(x) for x in coefs]
                pmCaps = [x(y[1]) for x,y in zip(pmCapFs, pmInfo)]

                maxCPUs = [x*0.9 for x in pmCaps]
                metisShares = [float(x)/sum(maxCPUs) for x in maxCPUs]
                print metisShares

                tpw=""
                for i in range(n):
                    tpw += str(i) + " = " + str(metisShares[i]) + "\n"
                print tpw
                tpwf = self.genFilename()
                self._write_to_file(tpwf, tpw)
                cmd = '%s -tpwgts=%s %s %d' % (self.toolCMD, tpwf, self.graph, n)
                self.logger.debug(cmd)
                outp = subprocess.check_output(cmd, shell=True)
                os.remove(tpwf)
            else:
                startT = time.time()
                cmd = '%s %s %d' % (self.toolCMD, self.graph, str(n))
                outp = subprocess.check_output([self.toolCMD + " " + self.graph + " " + str(n)], shell=True)
            self.logger.debug(outp)
            
            startT = time.time()
            self._parse_partition_result(self.graph + ".part." + str(n), n)
            os.remove(self.graph + ".part." + str(n))
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)


class MaxCPUPartitioner(MetisPartitioner):
    """
    C90 using share-based METIS Partitioner
    """
    def __init__(self, topo, tool=""):
        Partitioner.__init__( self, topo, tool="gpmetis -ptype=rb")

    def partition(self, alg="c90", capFs=None, pmInfo=None):

        # Create input file for METIS, removing the first swName
        self.graphFile = [x[1:] for x in self.graphFile]
        self.graphFile[0] = [len(self.switches), self.swLinks, "011 0"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)

        if capFs:
            print pmInfo
            print capFs
            n = len(pmInfo)
        else:
            n = 1
                
        if n > 1 and len(self.switches) > 1:
            if capFs:
                maxCPUs = [x[1] for x in pmInfo]
                metisShares = [float(x)/sum(maxCPUs) for x in maxCPUs]
                print metisShares

                tpw=""
                for i in range(n):
                    tpw += str(i) + " = " + str(metisShares[i]) + "\n"
                print tpw
                tpwf = self.genFilename()
                self._write_to_file(tpwf, tpw)
                cmd = '%s -tpwgts=%s %s %d' % (self.toolCMD, tpwf, self.graph, n)
                self.logger.debug(cmd)
                outp = subprocess.check_output(cmd, shell=True)
                os.remove(tpwf)
            else:
                startT = time.time()
                cmd = '%s %s %d' % (self.toolCMD, self.graph, str(n))
                outp = subprocess.check_output([self.toolCMD + " " + self.graph + " " + str(n)], shell=True)
            self.logger.debug(outp)
            
            startT = time.time()
            self._parse_partition_result(self.graph + ".part." + str(n), n)
            os.remove(self.graph + ".part." + str(n))
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)


class MaxCPUNPartitioner(MetisPartitioner):
    """
    C90 using share-based METIS Partitioner
    """
    def __init__(self, topo, tool=""):
        Partitioner.__init__( self, topo, tool="gpmetis -ptype=rb")

    def partition(self, alg="c90", capFs=None, pmInfo=None):

        # Create input file for METIS, removing the first swName
        self.graphFile = [x[1:] for x in self.graphFile]
        self.graphFile[0] = [len(self.switches), self.swLinks, "011 0"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)

        if capFs:
            print pmInfo
            print capFs
            n = len(pmInfo)
        else:
            n = 1
                
        if n > 1 and len(self.switches) > 1:
            if capFs:
                ### Scaler*MaxCPU ###
                maxCPUs = [x[0]*x[1] for x in pmInfo]
                metisShares = [float(x)/sum(maxCPUs) for x in maxCPUs]
                print metisShares

                tpw=""
                for i in range(n):
                    tpw += str(i) + " = " + str(metisShares[i]) + "\n"
                print tpw
                tpwf = self.genFilename()
                self._write_to_file(tpwf, tpw)
                cmd = '%s -tpwgts=%s %s %d' % (self.toolCMD, tpwf, self.graph, n)
                self.logger.debug(cmd)
                outp = subprocess.check_output(cmd, shell=True)
                os.remove(tpwf)
            else:
                startT = time.time()
                cmd = '%s %s %d' % (self.toolCMD, self.graph, str(n))
                outp = subprocess.check_output([self.toolCMD + " " + self.graph + " " + str(n)], shell=True)
            self.logger.debug(outp)
            
            startT = time.time()
            self._parse_partition_result(self.graph + ".part." + str(n), n)
            os.remove(self.graph + ".part." + str(n))
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)


class ChacoPartitioner(MetisPartitioner):
    """
    Chaco partitioner with multilevel KL
    """

    def __init__(self, topo, tool='~/Chaco-2.2/exec/chaco'): 
        Partitioner.__init__( self, topo, tool)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"

    def partition(self, n, alg="chaco", capFs=None, pmInfo=None):
        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)

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

    def __init__(self, topo, tool='~/Chaco-2.2-Siyuan/exec/chaco'): 
        Partitioner.__init__( self, topo, tool)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"

    def partition(self, n, alg="chacoUE", capFs=None, pmInfo=None):

        if capFs is None:
            self.logger.info('Shares are invalid!')
            sys.exit(0)

        ps = {x[0]:np.poly1d(x[1]) for x in capFs}
        maxCaps = [(x[0], int(ps[x[0]](80))) for x in capFs]
        topoW = simulatorFunc.checkTopo(self.topo)
        newCaps = simulatorFunc.adjustCap(topoW, maxCaps)
        selectedPMs = simulatorFunc.selectPMs(topoW, newCaps)
        # print selectedPMs
        newShares = [x[1] for x in selectedPMs]

        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        outputFile = uuid.uuid4()
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)
        # self.graph = self._write_to_file(pstr)

        inputPara = self.toolCMD+'.in'
        dim = int(ceil(log(n, 2)))
        caps = '\n'.join(map(str, newShares+[0]*(2**dim-n)))

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


class WFPartitioner(MetisPartitioner):
    '''
    Xiangyu's modified METIS
    '''
    def __init__(self, topo, tool='/home/cao/cs590-map/testbed_mapping_v4_2_1/main.py'): 
        Partitioner.__init__( self, topo, tool)
        # self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"

    def partition(self, n=1, alg='WF', capFs=None, pmInfo=None):

        # capFs: [(PM_NAME, [capFs])]
        # pmInfo: [(PM_NAME, [pmInfo])]
        # pmFile='/home/cao/cs590-map/testbed_mapping_v2/demo/pms.txt'
        outputDir = self.genFilename()
        os.makedirs(outputDir)
        ### Dump Mininet object to file ###
        self.graphFile[0] = [len(self.switches), self.swLinks ,'111']
        pstr = ''
        for line in self.graphFile:
            pstr = pstr + ' '.join(map(str, line)) + '\n'
        self.graph = '%s/input.graph' % outputDir
        self._write_to_file(self.graph, pstr)

        ### Create host CPU usage file ###
        hostCPUstr = ''
        for s in self.swHostCPU[1:]:
            hostCPUstr = hostCPUstr + '%d\n' % s[1]
        self.hostFile = '%s/input.host' % outputDir
        self._write_to_file(self.hostFile, hostCPUstr)

        pmStr = ''
        # for f in capFs:
        #     f[1].reverse()
        for i in range(len(pmInfo)):
            pmStr = pmStr + '%s %s\n' % (' '.join(map(str, pmInfo[i])), ' '.join(map(str, capFs[i])))
        pmFile = '%s/input.pm' % outputDir
        self._write_to_file(pmFile, pmStr)

        # -g GRAPH_FILE, --graph-file GRAPH_FILE
        #             File to read input graph from.
        # -p PM_FILE, --pm-file PM_FILE
        #                     File to read PM information.
        # -c VHOST_CPU_FILE, --vhost-cpu-file VHOST_CPU_FILE
        #                     File to read vhost CPU information.
        # -o OUT, --out OUT     If given, will generate output files to this dir.
        toolArgs = '-g %s -p %s -c %s -o %s' % (self.graph, pmFile, self.hostFile, outputDir)

        # subprocess.call('echo "'+self.graph+'\n'+self.graph+'.out\n1\n50\n2\n2\nn\n" > '+inputPara, shell=True)
        # subprocess.call('echo "'+self.chacoCtlPara+'" > User_Params', shell=True)
 
        # if n > 1 and len(self.switches) > 1:
        startT = time.time()
        outp = subprocess.check_output('%s %s' % (self.toolCMD, toolArgs), shell=True)
        #print "topo-partition:", time.time()-startT
        self.logger.debug(outp)
        self._write_to_file('%s/output.txt' % outputDir, outp)

        startT = time.time()
        self._parse_partition_result('%s/best_assignment_0.txt' % outputDir)
        #print "topo-reconstruct:", time.time()-startT
        # shutil.rmtree(outputDir)

        return Cluster(self.partitions,self.tunnels)


    def _parse_partition_result(self, filename):

        # for i in range(0, n):
        #     self.partitions.append(Topo())
        f = open(filename, 'r')
        cont = f.read().strip()
        lines = [x.strip() for x in cont.split()]

        # Add nodes from the output file
        i = 1
        for line in lines:
            part = int(line)
            numPart = len(self.partitions)
            if part + 1 > numPart:
                for k in range(part+1-numPart):
                    self.partitions.append(Topo())
            self.nodeToPart[self.pos[i]] = part
            # print 'part:', part, ',pos:', i, self.pos[i]
            self.partitions[part].addNode(self.pos[i], **self.topo.nodeInfo(self.pos[i]))
            i += 1
        f.close()
        startT = time.time()

        for hs in self.hostToSw:
            self.partitions[self.nodeToPart[self.hostToSw[hs]]].addNode(hs, **self.topo.nodeInfo(hs))
            self.partitions[self.nodeToPart[self.hostToSw[hs]]].addLink(**self.topo.linkInfo(hs, self.hostToSw[hs]))
            # self.partitions[self.nodeToPart[self.hostToSw[hs]]].addLink(hs, self.hostToSw[hs] , **self.topo.linkInfo(hs, self.hostToSw[hs]))

        #print "Metis-addNodes:", time.time()-startT
        startT = time.time()

        # Recover links and record tunnels
        for edge in self.topo.links():
            if (self.topo.isSwitch(edge[0]) and self.topo.isSwitch(edge[1])):
                if(self.nodeToPart[edge[0]] == self.nodeToPart[edge[1]]):
                    #print edge[0], edge[1], self.topo.linkInfo(edge[0],edge[1])
                    # self.partitions[self.nodeToPart[edge[0]]].addLink(edge[0], edge[1], **self.topo.linkInfo(edge[0],edge[1]))
                    self.partitions[self.nodeToPart[edge[0]]].addLink(**self.topo.linkInfo(edge[0],edge[1]))
                else:
                    self.tunnels.append([edge[0],edge[1], self.topo.linkInfo(edge[0], edge[1])])
        #print "Metis-addLinks:", time.time()-startT
        self.logger.debug('Topologies:')
        for t in self.partitions:
            self.logger.debug('Partition ' + str(self.partitions.index(t)))
            self.logger.debug('Nodes: ' + str(t.nodes()))
            self.logger.debug('Links: ' + str(t.links()))
        self.logger.debug('Tunnels: ' + str(self.tunnels))


class VoidPartitioner(WFPartitioner):
    def partition(self, n=1, alg='WF', capFs=None, pmInfo=None):
        self._parse_partition_result('/home/cao/mininet-hd/exp/ddos-rf36/WF-ex1.txt')
        #print "topo-reconstruct:", time.time()-startT
        # shutil.rmtree(outputDir)

        return Cluster(self.partitions,self.tunnels)


class ChacoUECapFPartitioner(MetisPartitioner):
    """
    Chaco partitioner with multilevel KL
    """

    def __init__(self, topo, tool='~/Chaco-2.2-Siyuan4/exec/chaco'): 
        Partitioner.__init__( self, topo, tool)
        self.chacoCtlPara = "OUTPUT_ASSIGN = TRUE\nOUTPUT_METRICS = -1\nPROMPT = FALSE\n"

    def partition(self, n, alg="chacoUECapF", capFs=None):

        if capFs is None:
            self.logger.info('Shares are invalid!')
            sys.exit(0)

        ### Dump Mininet object to file ###
        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
        pstr = ""
        for line in self.graphFile:
            pstr = pstr + " ".join(map(str, line)) + "\n"
        self.graph = self.genFilename()
        self._write_to_file(self.graph, pstr)

        ### Create host CPU usage file ###
        hostCPUstr = ''
        for s in self.swHostCPU[1:]:
            hostCPUstr = hostCPUstr + '%d\n' % s[1]

        self.hostFile = self.genFilename()
        self._write_to_file(self.hostFile, hostCPUstr)

        inputPara = self.toolCMD+'.in'
        dim = int(ceil(log(n, 2)))
        # caps = '\n'.join(map(str, shares+[0]*(2**dim-n)))
        # for f in shares:
        #     f[1].reverse()
        capFs = '\n'.join(' '.join(map(str, [int(y*10000) for y in x[1]])) for x \
            in capFs+[(None, [0]*len(capFs[0][1]))]*(2**dim-n))

        subprocess.call('echo "'+self.graph+'\n'+self.hostFile+'\n'+self.graph+'.out\n1\n50\n'+str(dim)+'\n'+capFs+'\n2\nn\n" > '
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
            os.remove(self.hostFile)
            os.remove(self.graph)
        else:
            self.partitions = [self.topo]
            
        return Cluster(self.partitions,self.tunnels)

#    def dumpGraph(self, fName):

#        self.graphFile[0] = [len(self.switches), self.swLinks ,"111"]
#        pstr = ""
#        for line in self.graphFile:
#            pstr = pstr + " ".join(map(str, line)) + "\n"
#        self.graph = self._write_to_file(pstr)

        ### Create host CPU usage file
#        hostCPUstr = ''
#        for s in self.swHostCPU[1:]:
#            hostCPUstr = hostCPUstr + '%d\n' % s[1]
#        self.hostFile = self._write_to_file(hostCPUstr)

        # inputPara = '%s-%s.in' % (self.toolCMD, fName)
        # dim = int(ceil(log(n, 2)))
        # caps = '\n'.join(map(str, shares+[0]*(2**dim-n)))
        # for f in shares:
        #     f[1].reverse()
        # capFs = '\n'.join(' '.join(map(str, [int(y*10000) for y in x[1]])) for x \
        #     in shares+[(None, [0]*len(shares[0][1]))]*(2**dim-n))

        # subprocess.call('echo "'+self.graph+'\n'+self.hostFile+'\n'+self.graph+'.out\n1\n50\n'\
        #     +str(dim)+'\n'+capFs+'\n2\nn\n" > '+inputPara, shell=True)
#        subprocess.call('cp %s %s.graph' % (self.graph, fName), shell=True)
#        subprocess.call('cp %s %s.host' % (self.hostFile, fName), shell=True)



class MininetPartitioner(Partitioner):
    """
    Wrapper of Mininet placers
    """
    def __init__(self, topo, tool=''): 
        Partitioner.__init__( self, topo)
        self.placers = {'mn-random': RandomPlacer, 'MN-RRP': RoundRobinPlacer,
                'MN-SBP':SwitchBinPlacer, 'mn-hostSwitchBin':HostSwitchBinPlacer}

    def partition(self, n=6, alg='WF', capFs=None, pmInfo=None):

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
                # self.partitions[self.nodeToPart[link[0]]].addLink(link[0],link[1],**self.topo.linkInfo(link[0],link[1]))
                self.partitions[self.nodeToPart[link[0]]].addLink(**self.topo.linkInfo(link[0],link[1]))

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

