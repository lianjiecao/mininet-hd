#! /usr/bin/python2.7

import os, sys, time, operator, math, random, logging
# import termcolor as T
from collections import defaultdict
import numpy as np
import argparse, subprocess, multiprocessing

from mininet.cli import CLI
from mininet.topo import Topo, LinearTopo
from mininet.net import Mininet
from mininet.node import UserSwitch, OVSSwitch, IVSSwitch, RemoteController, CPULimitedHost
from mininet.link import TCLink

from MaxiNet.Frontend import maxinet

from dijkstra import DGraph, dijsktraCompute
sys.path.append('/home/cao/mininet-hd/simulator')
from topoSet import TopoSet
from partitioner import C90Partitioner, ChacoUEPartitioner, ChacoUECapFPartitioner, \
    MininetPartitioner, WFPartitioner, VoidPartitioner, MaxCPUPartitioner, MaxCPUNPartitioner
import simulatorFunc


logLevel = logging.DEBUG
# logLevel = logging.INFO
logger = logging.getLogger('ddos-exp')
logger.setLevel(logLevel)
ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-5s:%(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.propagate = False


homeDir = '/home/cao/mininet-hd/exp/ddos-rf36/'
# logger.basicConfig(format='%(asctime)s %(message)s')
# logger.setLevel(logging.DEBUG)

partitioners = {
    'C90':C90Partitioner,
    # 'chaco':ChacoPartitioner,
    'UC-MKL':ChacoUEPartitioner,
    'UC-MKL2':ChacoUECapFPartitioner,
    # 'mn-random':mnPartitioner,
    'MN-SBP':MininetPartitioner,
    'WF': WFPartitioner,
    # 'mn-switchBin':mnPartitioner,
    # 'mn-hostSwitchBin':mnPartitioner,
    'VOID': VoidPartitioner,
    'MAX_CPU':MaxCPUPartitioner,
    'MAX_CPU_N':MaxCPUNPartitioner,
    }

# Max capacity: {'cap34':1400, 'cap35':800, 'cap36':500}
# PMCap = {'cap34':1120, 'cap35':640, 'cap36':440}
# PMIdx = {'cap34':0, 'cap35':1, 'cap36':2}

def partitionTopo_old(topo, PMInfo, p):

    # PMInfo: {pm_name: [pm_idx, [pm_cap_func]], ...}
    logger.info('+++++ Mapping algorithm: %s +++++', p)
    mapping = {}
    # ps = {x:np.poly1d(PMInfo[x][1]) for x in PMInfo} 
    # capFs = sorted(PMCapFs.items(), key=operator.itemgetter(1), reverse=True)
    # capFsSorted = sorted([(x, PMInfo[x][1]) for x in PMInfo], key=lambda x: ps[x[0]](100), reverse=True) # [(pm_name, capFs)]

    ps = {x:np.poly1d(PMInfo[x][-1]) for x in PMInfo} # {pm_name:poly1d_object}
    capFsSorted = sorted([(x, PMInfo[x][-1]) for x in PMInfo], key=lambda x: ps[x[0]](PMInfo[x[0]][1]), reverse=True)
    pmInfo = sorted([(x, PMInfo[x][1:-1]) for x in PMInfo], key=lambda x: ps[x[0]](PMInfo[x[0]][1]), reverse=True)
    logger.info('Cap functions sorted:')
    for f in capFsSorted:
        logger.info('- %s:%s', f[0], f[1])

    PMIdx = {x:PMInfo[x][0] for x in PMInfo}
    # maxCaps = [(x[0], int(ps[x[0]](80))) for x in capFs]
    # topoW = simulatorFunc.checkTopo(topo)
    # newCaps = simulatorFunc.adjustCap(topoW, maxCaps)
    # selectedPMs = simulatorFunc.selectPMs(topoW, newCaps)

    # topoW = simulatorFunc.checkTopo(topo)
    # newCaps = simulatorFunc.adjustCapFs(topoW, capFs)
    # selectedPMs = simulatorFunc.selectPMs(topoW, newCapFs)
    # print selectedPMs
    parti = partitioners[p](topo)
    # ret = parti.partition(len(selectedPMs), alg=p, shares=[x[1] for x in selectedPMs])
    ret = parti.partition(alg=p, capFs=capFsSorted, pmInfo=pmInfo)

    subTopos = ret.getTopos()

    for i in range(len(subTopos)):
        for n in subTopos[i].nodes():
            mapping[n] = PMIdx[capFsSorted[i][0]]

        logger.info('Partition: %d, pm: %s, nodes: %d, links: %d' % \
            (PMIdx[capFsSorted[i][0]], capFsSorted[i][0], len(subTopos[i].nodes()), len(subTopos[i].links())))
        logger.debug('    - nodes: %d %s' % (len(subTopos[i].nodes()), subTopos[i].nodes()))
        logger.debug('    - links: %d %s' % (len(subTopos[i].links()), subTopos[i].links()))
    return mapping


def partitionTopo(topo, PMInfo, alg):

    # PMInfo: {pm_name: [pm_idx, [pm_cap_func]], ...}
    logger.info('+++++ Mapping algorithm: %s +++++', alg)
    mapping = {}

    ps = {x:np.poly1d(PMInfo[x][-1]) for x in PMInfo} # {pm_name:poly1d_object}
    capFsSorted = sorted([(x, PMInfo[x][-1]) for x in PMInfo], key=lambda x: ps[x[0]](PMInfo[x[0]][1]), reverse=True)
    pmInfo = sorted([(x, PMInfo[x][1:-1]) for x in PMInfo], key=lambda x: ps[x[0]](PMInfo[x[0]][1]), reverse=True)
    # logger.info('Cap functions sorted:')
    # for f in capFsSorted:
    #     logger.info('- %s:%s', f[0], f[1])

    PMIdx = {PMInfo[x][0]:x for x in PMInfo}
    # maxCaps = [(x[0], int(ps[x[0]](80))) for x in capFs]
    # topoW = simulatorFunc.checkTopo(topo)
    # newCaps = simulatorFunc.adjustCap(topoW, maxCaps)
    # selectedPMs = simulatorFunc.selectPMs(topoW, newCaps)

    # topoW = simulatorFunc.checkTopo(topo)
    # newCaps = simulatorFunc.adjustCapFs(topoW, capFs)
    # selectedPMs = simulatorFunc.selectPMs(topoW, newCapFs)
    # print selectedPMs
    PMInfoList = []
    # for pm in PMInfo:
    ### [[PM_idx, PM_params, capFunc_coef], ...]
    PMInfoList = sorted([[PMInfo[x][0], PMInfo[x][1:-1], PMInfo[x][-1]] for x in PMInfo], key=lambda x: x[0])
    parti = partitioners[alg](topo)
    # ret = parti.partition(len(selectedPMs), alg=alg, shares=[x[1] for x in selectedPMs])
    ret = parti.partition(alg=alg, capFs=[x[2] for x in PMInfoList], pmInfo=[x[1] for x in PMInfoList])
    subTopos = ret.getTopos()

    for i in range(len(subTopos)):
        for n in subTopos[i].nodes():
            mapping[n] = i

        logger.info('Partition: %d, pm: %s, nodes: %d, links: %d' % \
            (i, PMIdx[i], len(subTopos[i].nodes()), len(subTopos[i].links())))
        logger.debug('    - nodes: %d %s' % (len(subTopos[i].nodes()), subTopos[i].nodes()))
        logger.debug('    - links: %d %s' % (len(subTopos[i].links()), subTopos[i].links()))
    return mapping


def parseTrace(pm, bwmTrace, cpuTrace, outputFile, intfs=['total']):
    # Type rate:
    # unix timestamp;iface_name;bytes_out/s;bytes_in/s;bytes_total/s;bytes_in;bytes_out;packets_out/s;packets_in/s;
    # packets_total/s;packets_in;packets_out;errors_out/s;errors_in/s;errors_in;errors_out\n
    logger.info('')
    logger.info('+++++ parseTrace +++++')
    logger.debug('Parsing trace files of %s ...', pm)

    if bwmTrace:
        bwmCont = subprocess.check_output("grep -E '%s' %s" % ('|'.join(intfs), bwmTrace), shell=True).split('\n')
        tx, rx = {}, {}
        # startTime, endTime = int(bwmCont[10].split(';')[0]), int(bwmCont[-10].split(';')[0])
        for line in bwmCont[:-1]:
            tokens = line.split(';')
            tx.setdefault(tokens[1], []).append(float(tokens[2])*8/1000000)
            rx.setdefault(tokens[1], []).append(float(tokens[3])*8/1000000)

    if cpuTrace:
        cpuCont = subprocess.check_output("awk 'NR > 3' %s | awk '{print $13}'" % (cpuTrace), shell=True).split('\n')
        cpuUtils = [100-float(x) for x in cpuCont[:-1]]

    if outputFile:
        # More readable output
        # outputFile.write('  %s:tx %d \n  %s:rx %d \n  %s:pkt_out %d \n  %s:pkt_in %d \n  cpu %d \n' % (
        #     intf, sum(rates['tx'])/len(rates['tx']), intf, sum(rates['rx'])/len(rates['rx']), 
        #     intf, sum(rates['pkt_out'])/len(rates['pkt_out']), intf, sum(rates['pkt_in'])/len(rates['pkt_in']),
        #     round(sum(cpuUtils)/len(cpuUtils))))

        # More parsable output
        # tx rx pkt_out pkt_in cpu
        # outputFile.write('%d %d %d %d %d\n' % (
        #     sum(rates['tx'])/len(rates['tx']), sum(rates['rx'])/len(rates['rx']), 
        #     sum(rates['pkt_out'])/len(rates['pkt_out']), sum(rates['pkt_in'])/len(rates['pkt_in']),
        #     round(sum(cpuUtils)/len(cpuUtils))))

        if bwmTrace:
            for intf in sorted(tx.keys()):
                # print intf+':tx %.3f' % (sum(tx[intf])/len(tx[intf]))
                # print intf+':rx %.3f' % (sum(rx[intf])/len(rx[intf]))
                outputFile.write('%s-%s:tx %s\n' % (pm, intf, ' '.join(['%.2f' % (x) for x in tx[intf]])))
                outputFile.write('%s-%s:rx %s\n' % (pm, intf, ' '.join(['%.2f' % (x) for x in rx[intf]])))
        if cpuTrace:
        # print 'cpu', round(sum(cpuUtils)/len(cpuUtils))
            outputFile.write('%s-cpu %s\n\n' % (pm, ' '.join(['%.2f' % (x) for x in cpuUtils])))
    else:
        if bwmTrace:
            for intf in sorted(tx.keys()):
                # print intf+':tx %.3f' % (sum(tx[intf])/len(tx[intf]))
                # print intf+':rx %.3f' % (sum(rx[intf])/len(rx[intf]))
                print '%s:tx-%s %s' % (intf, pm, ' '.join(['%.2f' % (x) for x in tx[intf]]))
                print '%s:rx-%s %s' % (intf, pm, ' '.join(['%.2f' % (x) for x in rx[intf]]))
        if cpuTrace:
        # print 'cpu', round(sum(cpuUtils)/len(cpuUtils))
            print 'cpu-%s %s' % (pm, ' '.join(['%.2f' % (x) for x in cpuUtils]))


def genPolygraphFile(origF, srvIP, cltIP='127.0.0.1', rate=1):
    f = open(origF, 'r')
    fName = os.tempnam()
    newF = open(fName,'w')
    cont = f.read()
    newCont = cont.replace("addresses = ['127.0.0.1:8888'];", "addresses = ['%s:8888'];" % (srvIP)). \
        replace("addresses = ['127.0.0.1'];", "addresses = ['%s' ** %d];" % (cltIP, rate))
    newF.write(newCont)
    newF.close()
    f.close()

    return fName


def convertToDOT(topo):
    for l in topo.links():
        print  '    %s -- %s;' % (l[0],l[1]) #, topo.linkInfo(l[0], l[1])


def checkSwitchDegree(topo, d=2, verbose=False):
    '''
    Check the degree of switches in the topology and return a list of switches with degree <= d 
    and a dictionary {switch: degree}
    '''
    swDegree = {}
    linkEnds = []
    hostSw = []
    for l in topo.links():
        linkEnds += l
    for s in topo.switches():
        swDegree[s] = linkEnds.count(s)
        if swDegree[s] <= d:
            hostSw.append(s)
        if verbose:
            print s, swDegree[s]
    return hostSw, swDegree


def checkTopo(topo):
    '''
    Print topology information: hosts, switches, and links
    '''
    logger.info('')
    logger.info('+++++ checkTopo +++++')
    logger.info('--- Hosts: %d ---' % len(topo.hosts()))
    logger.info('%s' %  ' '.join(topo.hosts()))
    logger.info('--- Switches: %d ---' % len(topo.switches()))
    logger.info('%s' % ' '.join(topo.switches()))
    logger.info('--- Links: %d ---' % len(topo.links()))
    for l in topo.links(sort=True, withInfo=True):
        logger.info('[%s, %s] %s' % (l[0], l[1], l[2]))
    # print 'Links:', len(topo.links()), topo.links(sort=True, withInfo=True) #withKeys=True, 


def addHosts(topo, swList, bw):
    '''
    Add one host to each switch in swList 
    '''
    logger.debug('')
    logger.debug('+++++ addHosts +++++')
    hs = []
    for sw in swList:
        hIdex = sw[1:] # assume the name of switch is sXX
        h = 'h' + hIdex
        hs.append(h)
        if h not in topo.hosts():
            topo.addHost(h, ip='10.0.0.'+hIdex, cls=CPULimitedHost, cpu=0.1)
            topo.addLink(h, sw, bw=bw, delay='1ms')
    logger.debug('Add hosts: [%s]', ' '.join(hs))


def addEdgeHosts(topo, bw=10, d=1):
    '''
    Get the list of edge switches (degree <= d) and add host to each of them
    '''
    logger.debug('')
    logger.debug('+++++ addEdgeHosts +++++')
    [edgeSws, tmp] = checkSwitchDegree(topo, d)
    addHosts(topo, edgeSws, bw)
    


def assignWebSw(topo):
    '''
    Randomly select on switch with median degree value ([median-1, median+1])
    '''
    logger.debug('')
    logger.debug('+++++ assignWebSw +++++')
    [tmp, swDegree] = checkSwitchDegree(topo, verbose=False)
    sortedSwDegree = sorted(swDegree.items(), key=operator.itemgetter(1), reverse=True)
    for sw in sortedSwDegree:
        # logger.debug('%s: %d' % (sw[0], sw[1]))
        logger.debug('%-3s:%d', sw[0], sw[1])
    logger.debug('%d - %s', len(sortedSwDegree), sortedSwDegree)
    degreeMedian = int(np.median(list(set([x[1] for x in sortedSwDegree]))))
    degreeMedianSet = [degreeMedian-1, degreeMedian, degreeMedian+1]
    tmpStart, tmpEnd = len(sortedSwDegree)/4, len(sortedSwDegree)-len(sortedSwDegree)/4
    webSwCandid = [x for x in sortedSwDegree if x[1] in degreeMedianSet]
    webSrvSw = random.choice(webSwCandid)
    logger.debug('Selected degrees : [%s]', ' '.join(map(str, degreeMedianSet)))
    logger.debug('Selected webSrvSw: %s, candidates: %s', webSrvSw, ' '.join(map(str, webSwCandid)))

    return webSrvSw

def findNeighbors(topo, node):
    '''
    Find the neighbors of a given node
    '''
    logger.debug('')
    logger.debug('+++++ findNeighbors +++++')
    nbs = []
    for l in topo.links():
        if node in l:
            nbs.extend([x for x in l if x != node])
    logger.debug('Node: %s, neighbors: [%s]', node, ' '.join(nbs))
    return nbs


def computePath(topo, srcVert, verbose=False):
    '''
    Use Dijkstra algorithm to compute path 
    '''

    logger.debug('')
    logger.debug('+++++ computePath +++++')
    g = DGraph()
    # print srcVert
    for n in topo.nodes():
        # print n
        g.addVert(n)
    for l in topo.links():
        g.addEdge(l[0], l[1], 1)
    [v, p] = dijsktraCompute(g, srcVert)

    # print p
    paths = {}
    for n in topo.nodes():
        paths[n] = []
        currVert = n
        while currVert != srcVert:
            paths[n].append(currVert)
            currVert = p[currVert]
        paths[n].append(srcVert)
        if verbose:
            logger.info('%s', ' => '.join(paths[n]))

    return paths


def assignAttackerVictim(topo, webSw):
    '''
    Assign victim clients, attack senders and recievers
    '''

    logger.debug('')
    logger.debug('+++++ assignAttackerVictim +++++')
    # Compute paths from edge hosts to web switch
    # Break paths into links and count frequencies links are shared
    pathsToWebSrv = computePath(topo, webSw)
    linksToWebSw = {} # (link tuple):[list of hosts share this link]
    webClts = []
    logger.debug('Paths to web server switch: %s', webSw)
    for p in pathsToWebSrv:
        if 'h' in p:
            logger.debug('  %s', ' => '.join(pathsToWebSrv[p]))
            for i in range(len(pathsToWebSrv[p])-1):
                linksToWebSw.setdefault(tuple(sorted([pathsToWebSrv[p][i], pathsToWebSrv[p][i+1]])), []).\
                    append(pathsToWebSrv[p][0])
    logger.debug('Link stats:')
    for l in sorted(linksToWebSw, key=lambda l:len(linksToWebSw[l]), reverse=True):
        logger.debug('  %s %d %s', l, len(linksToWebSw[l]), linksToWebSw[l])

    # Find the neighbors of web switch as candidats of attack receiver
    # Compute paths from edge hosts to attack receiver candidats
    webSwNbs = findNeighbors(topo, webSw)
    pathsToWebNbs = {}
    for sw in webSwNbs:
        pathsToWebNbs[sw] = computePath(topo, sw)
    logger.debug('Attack receiver candidates: %s', ' '.join(webSwNbs))

    # 
    attackers = {} # attack sender: [len of path to attack receiver, attack receiver switch]
    for l in sorted(linksToWebSw.items(), key=lambda l:len(l[1]), reverse=False): # linksToWebSw.items():
        if len(l[1]) > 1:
            logger.debug('Link: %s, shared by %d hosts: %s', l[0], len(l[1]), ' '.join(l[1]))
            tmpNum = 0
            attackerAdded = False
            for h in l[1]:
                logger.debug('  Host: %s' % h)
                for sw in pathsToWebNbs:
                    if l[0][0] in pathsToWebNbs[sw][h] and l[0][1] in pathsToWebNbs[sw][h] and tmpNum < len(l[1])/2 and h not in webClts:
                        # Link l is shared by the path from sw (attack receiver candidate) to h (edge host)
                        tmpNum += 1
                        if h not in attackers or pathsToWebNbs[sw][h][-1] not in [x[-1] for x in attackers[h]]:
                            # h is not assigned as attacker sender or receiver before
                            attackers.setdefault(h, []).append([len(pathsToWebNbs[sw][h]), sw])
                            attackerAdded = True
                            logger.debug('    * Selected: %s' % '=>'.join(pathsToWebNbs[sw][h]))
                            logger.debug('    Path to web server: %s' % '=>'.join(pathsToWebSrv[h]))
                            break

            if attackerAdded:
                # For hosts sharing the same toWebSrv link, assign the rest of edge hosts (except attackers) as web clients
                # If none of the hosts is assigned as attacker, then none of them should be assigned as web clients neither
                webClts.extend([x for x in l[1] if x not in attackers and x not in webClts])
            logger.debug('Attackers: %s' % attackers)
            logger.debug('WebClients:%s' % webClts)

    # Add hosts for web server and attack servers
    # attackPairs: (attacking host, attacking receiver)
    attackPairs = [tuple([y[0], x[1].replace('s','h')]) for y in attackers.items() for x in y[1]]

    return [attackPairs, webClts]


def addLocalFlowRules(topo, exp=None, dumpFlows=False):
    '''
    Install rules for each link to make sure neighbor hosts can reach each other
    This is used for generating TCP background traffic
    '''
    logger.debug('')
    logger.debug('+++++ addLocalFlowRules +++++')
    SwHLinks = {}
    SwSwLinks = {}
    tunnels = [sorted([x[0], x[1]]) for x in exp.topology.getTunnels()]
    # print tunnels
    for l in topo.links(sort=True, withInfo=True):
        # Find the new names of interfaces if the link is a tunnel
        # O.w., the interface name is related to the port number
        # l: ('h17', 's17', {'delay': '1ms', 'bw': 50, 'node1': 'h17', 'node2': 's17', 'port2': 13, 'port1': 0})
        if sorted([l[0], l[1]]) in tunnels:
            intf1 = intf2 = exp.tunnellookup[(l[0], l[1])]
        else:
            intf1, intf2 = '%s-eth%d' % (l[2]['node1'], l[2]['port1']), '%s-eth%d' % (l[2]['node2'], l[2]['port2'])
        # Use the interface name to locate the related port number (deal with tunnels)
        port1 = exp.get_node(l[0]).intfNames().index(intf1)
        port2 = exp.get_node(l[1]).intfNames().index(intf2)
        logger.debug('Link: %s %s %s - %s %s %s', l[2]['node1'], l[2]['port1'], intf1, l[2]['node2'], l[2]['port2'], intf2)

        if not topo.isSwitch(l[0]):
        # For a switch--host link, keep the switch port that connects to host
            # SwHLinks[l[1]] = [l[0], topo.nodeInfo(l[0])['ip'], port2, l[2]['port2']]
            SwHLinks[l[1]] = {'host':l[0], 'hostIP':topo.nodeInfo(l[0])['ip'], 'portToHost':port2, 'oldPort':l[2]['port2']}
            logger.debug('Sw - host: %s', SwHLinks[l[1]])
        elif not topo.isSwitch(l[1]):
            # SwHLinks[l[0]] = [l[1], topo.nodeInfo(l[1])['ip'], port2, l[2]['port2']]
            SwHLinks[l[0]] = {'host':l[1], 'hostIP':topo.nodeInfo(l[1])['ip'], 'portToHost':port2, 'oldPort':l[2]['port2']}
            logger.debug('Sw - host: %s', SwHLinks[l[0]])
        else:
        # For switch--switch link, install rules on both switches 
            for proto in ['arp', 'ip']: 
                # Install rules on node1
                logger.debug('- Install rules on %s', l[0])
                cmdIn = 'sudo dpctl add-flow unix:/tmp/%s %s,nw_src=%s,nw_dst=%s,idle_timeout=0,actions=output:%s' \
                    % (l[0], proto, SwHLinks[l[1]]['hostIP'], SwHLinks[l[0]]['hostIP'], SwHLinks[l[0]]['portToHost'])
                cmdOut = 'sudo dpctl add-flow unix:/tmp/%s %s,nw_src=%s,nw_dst=%s,idle_timeout=0,actions=output:%s' \
                    % (l[0], proto, SwHLinks[l[0]]['hostIP'], SwHLinks[l[1]]['hostIP'], port1)
                logger.debug('  - %s', cmdIn)
                logger.debug('  - %s', cmdOut)
                exp.node_to_worker[l[0]].run_cmd(cmdIn)
                exp.node_to_worker[l[0]].run_cmd(cmdOut)

                # Install rules on node2
                logger.debug('  - Install rules on %s', l[1])
                cmdIn = 'sudo dpctl add-flow unix:/tmp/%s %s,nw_src=%s,nw_dst=%s,idle_timeout=0,actions=output:%s' \
                    % (l[1], proto, SwHLinks[l[0]]['hostIP'], SwHLinks[l[1]]['hostIP'], SwHLinks[l[1]]['portToHost'])
                cmdOut = 'sudo dpctl add-flow unix:/tmp/%s %s,nw_src=%s,nw_dst=%s,idle_timeout=0,actions=output:%s' \
                    % (l[1], proto, SwHLinks[l[1]]['hostIP'], SwHLinks[l[0]]['hostIP'], port2)

                logger.debug('  - %s', cmdIn)
                logger.debug('  - %s', cmdOut)
                exp.node_to_worker[l[1]].run_cmd(cmdIn)
                exp.node_to_worker[l[1]].run_cmd(cmdOut)

    if dumpFlows:
        for sw in topo.switches():
            logger.debug('--- %s ---', sw)
            logger.debug(exp.node_to_worker[sw].run_cmd('sudo dpctl dump-flows unix:/tmp/' + sw))

    return SwHLinks


def addLocalBCRules(topo, exp, dumpFlows=False):
    '''
    Add one hop broadcast rules to all switches for background broadcast traffic
    '''

    logger.info('')
    logger.info('+++++ addLocalBCRules +++++')

    for s in topo.switches():
        cmd1 = 'sudo dpctl add-flow unix:/tmp/%s ip,nw_dst=10.255.255.255,nw_tos=0x0,idle_timeout=0,actions=mod_nw_tos:5,all' % s
        # cmd2 = 'sudo dpctl add-flow unix:/tmp/%s ip,nw_dst=10.255.255.255,nw_tos=0x4,idle_timeout=0,actions=normal' % s
        logger.debug('  - %s', cmd1)
        # logger.debug('    - %s', cmd2)
        exp.node_to_worker[s].run_cmd(cmd1)
        # exp.node_to_worker[s].run_cmd(cmd2)
    return


def testLocalFlowRules(topo, SwHLinks, exp):
    '''
    Test installed flow rules for each link
    '''

    logger.debug('')
    logger.debug('+++++ testLocalFlowRules +++++')
    logger.info('Testing local link connectivity ...')
    for l in topo.links():
        if l[0] in SwHLinks and l[1] in SwHLinks:
            h1, h2 = SwHLinks[l[0]]['host'], SwHLinks[l[1]]['host']
            logger.debug('%s => %s', h1, h2)
            logger.debug(exp.get_node(h1).cmd('ping -c 3 %s' % (exp.get_node(h2).IP())))
            if exp.get_node(h1).cmd('echo $?').strip() != '0':
                logger.warning('%s => %s test failed!!!', h1, h2)
            # exp.get_node(SwHLinks[l[0]][0]).cmd('iperf -s -i 1 &')
            # print exp.get_node(SwHLinks[l[1]][0]).cmd('iperf -c %s -t 10 -i 1' % (exp.get_node(SwHLinks[l[0]][0]).IP()))


def addPathFlowRules(topo, exp, path):
    '''
    Install rules to all switches on a path
    '''

    logger.debug('')
    logger.debug('+++++ addPathFlowRules +++++')
    logger.debug('Install rules for path: %s', ' => '.join(path))
    nodeWPorts = {}
    tunnels = [sorted([x[0], x[1]]) for x in exp.topology.getTunnels()]
    intfs = []

    # Find in and out ports on the same switch
    for i in range(0, len(path)-1):
        origPorts = topo.port(path[i], path[i+1])
        if sorted([path[i], path[i+1]]) in tunnels:
            intf1 = intf2 = exp.tunnellookup[(path[i], path[i+1])]
            intfs.append(intf1)
        else:
            intf1, intf2 = '%s-eth%d' % (path[i], origPorts[0]), '%s-eth%d' % (path[i+1], origPorts[1])
            intfs.extend([intf1, intf2])
        port1 = exp.get_node(path[i]).intfNames().index(intf1)
        port2 = exp.get_node(path[i+1]).intfNames().index(intf2)

        # ports = topo.port(path[i], path[i+1])
        nodeWPorts.setdefault(path[i], []).append(port1)
        nodeWPorts.setdefault(path[i+1], []).append(port2)

    ip1, ip2 = topo.nodeInfo(path[0])['ip'], topo.nodeInfo(path[-1])['ip']
    logger.debug('NodesWPorts: %s' % nodeWPorts)
    for sw in path[1:-1]:
        # logger.debug('%s %s' % (sw, nodeWPorts[sw]))
        for proto in ['arp', 'ip']: # 
            # Install rules on sw
            cmd1 = 'sudo dpctl add-flow unix:/tmp/%s %s,nw_src=%s,nw_dst=%s,idle_timeout=0,actions=output:%s' \
                % (sw, proto, ip1, ip2, nodeWPorts[sw][1])
            cmd2 = 'sudo dpctl add-flow unix:/tmp/%s %s,nw_src=%s,nw_dst=%s,idle_timeout=0,actions=output:%s' \
                % (sw, proto, ip2, ip1, nodeWPorts[sw][0])
            logger.debug('- Install rules on %s', sw)
            logger.debug('  - %s', cmd1)
            logger.debug('  - %s', cmd2)
            exp.node_to_worker[sw].run_cmd(cmd1)
            exp.node_to_worker[sw].run_cmd(cmd2)
    print intfs
    return intfs


def testPathFlowRules(exp, path):
    '''
    Test installed flow rules for paths
    '''

    logger.debug('')
    logger.debug('+++++ testPathFlowRules +++++')
    logger.debug('%s => %s', path[0], path[-1])
    logger.debug(exp.get_node(path[0]).cmd('ping -c 3 %s' % (exp.get_node(path[-1]).IP())))
    if exp.get_node(path[0]).cmd('echo $?').strip() != '0':
        logger.warning('%s => %s test failed!!!', path[0], path[-1])
    # exp.get_node(path[0]).cmd('iperf -s -i 1 &')
    # print exp.get_node(path[-1]).cmd('iperf -c %s -t 10 -i 1' % (exp.get_node(path[0]).IP()))

    
def startBwm(topo, exp):
    '''
    Start bwm-ng for throughput monitoring, excluding links between hosts and switchs
    '''

    logger.info('')
    logger.info('+++++ startBwm +++++')

    nicsToExclude = []
    for l in topo.links(sort=True, withInfo=True):
        # print l
        if topo.isSwitch(l[0]) and not topo.isSwitch(l[1]):
            # print l[0], exp.get_node(l[0]).intfNames()
            nicsToExclude.append('%s-eth%d' % (l[0], l[2]['port1']))
        elif topo.isSwitch(l[1]) and not topo.isSwitch(l[0]):
            # print l[1], exp.get_node(l[1]).intfNames()
            nicsToExclude.append('%s-eth%d' % (l[1], l[2]['port2']))

    swIntfs = {}
    # print nicsToExclude
    for worker in exp.cluster.workers():
        wName = worker.hn()
        swIntfs[wName] = [x for x in worker.run_cmd("ip link list | grep s[0123456789]*-eth | awk -F '[ @]' '{print $2}'")\
            .split() if x not in nicsToExclude]
        logger.info('Monitering veths on %s: [%s]', wName, ' '.join(swIntfs[wName]))
        bwmTraces = '/tmp/bwm-out-%s.log' % (wName)
        bwmCmd = 'rm %s;bwm-ng -t 1000 -o csv -T rate -F %s -I %s' % (bwmTraces, bwmTraces, ','.join(swIntfs[wName]+['em1']))
        worker.daemonize(bwmCmd)
    return swIntfs


def startBCTraffic(topo, exp, pathsToAvoid, bw, bcLen, traceFiles):
    '''
    Start broadcast UDP traffic as background traffic
    '''
    logger.info('')
    logger.info('+++++ startBCTraffic +++++')
    logger.debug('Starting broadcast traffic ...')
    pktSize = 1250
    pktInt = int(10**6 * pktSize * 8 / (bw * 10**6)) # bw in Mbps

    if pathsToAvoid:
        hostsToAvoid = []
        for p in pathsToAvoid:
            hostsToAvoid.extend([x.replace('s', 'h') for x in [p[1], p[-1]]])
        hostsToUse = [x for x in topo.hosts() if x not in hostsToAvoid]
    else:
        hostsToUse = topo.hosts()

    for h in hostsToUse:
        fileName = '/tmp/hping3-bg-udp-client-%s.out' % h
        # print exp.get_node(h).cmd('ifconfig')
        cmdHping3 = 'sudo hping3 10.255.255.255 --quiet --data 1250 --interval u%d --udp -p 8888 --ttl 2 1>/dev/null 2>%s &' % (pktInt, fileName)
        # cmdHping3 = 'sudo hping3 10.255.255.255 --quiet --data 1250 --interval u1 --udp -p 8888 --ttl 2 1>/dev/null 2>%s &' % (fileName)
        cmdKill = 'echo "sleep %d; sudo pkill hping3;" > kill-hping3-bc.sh; bash kill-hping3-bc.sh &' % (bcLen)
        exp.get_node(h).cmd(cmdHping3, shell=True)
        exp.get_node(h).cmd(cmdKill, shell=True)
        # "sudo hping3 -2 -q -p 8889 -i u$INT -d 64 ${UDP_VMs[0]} 1>/dev/null 2>hping3.stat & sleep $RunTime; sudo pkill hping3;"
        traceFiles.setdefault(h, []).append(fileName)
        logger.debug('- %s', h)
        logger.debug('  - %s',cmdHping3)
    return


def startBGTraffic(topo, exp, pathsToAvoid, bw, bgLen, traceFiles):
    '''
    Start TCP background taffic on all hosts
    '''

    if pathsToAvoid:
        linksToAvoid = []
        for p in pathsToAvoid:
            linksToAvoid.extend(zip(p, p[1:]))
        linksToUse = [x for x in [tuple(sorted(x)) for x in topo.links()] if x not in linksToAvoid]
    else:
        linksToUse = topo.links()

    logger.info('')
    logger.info('+++++ startBGTraffic +++++')
    logger.debug('Starting background traffic ...')
    bgTrafficSrv = []
    for h in topo.hosts():
        # exp.get_node(h).cmd('iperf -s -i 1 > /tmp/iperf-bg-tcp-server-%s.out &' % h)
        fileName = '/tmp/iperf-bg-udp-server-%s.out' % h
        exp.get_node(h).cmd('iperf -s -u -i 1 > %s &' % fileName)
        traceFiles.setdefault(h, []).append(fileName)
        bgTrafficSrv.append(h)

    time.sleep(1)

    for l in linksToUse:  # topo.links():
        ### Find switch links, start TCP traffic between the hosts attached to the two switches
        if topo.isSwitch(l[0]) and topo.isSwitch(l[1]):
            hosts = [x.replace('s', 'h') for x in l]
            logger.debug('  - (%s)', ', '.join(hosts))
            # exp.get_node(hosts[1]).cmd('iperf -c %s -t %d -l 1250 -i 1 &' % (exp.get_node(hosts[0]).IP(), bgLen))
            # exp.get_node(hosts[0]).cmd('iperf -c %s -t %d -l 1250 -i 1 &' % (exp.get_node(hosts[1]).IP(), bgLen))
            fileName = '/tmp/iperf-bg-udp-client-%s.out' % '-'.join([hosts[0],hosts[1]])
            iperfCmd = 'iperf -c %s -u -t %d -l 1250 -b %dm -i 1 > %s &' % (exp.get_node(hosts[1]).IP(), bgLen, bw, fileName)
            exp.get_node(hosts[0]).cmd(iperfCmd)
            traceFiles.setdefault(hosts[0], []).append(fileName)

            # fileName = '/tmp/iperf-bg-udp-client-%s.out' % '-'.join([hosts[1],hosts[0]])
            # iperfCmd = 'iperf -c %s -u -t %d -l 1250 -b %dm -i 1 > %s &' % (exp.get_node(hosts[0]).IP(), bgLen, bw, fileName)
            # exp.get_node(hosts[1]).cmd(iperfCmd)
            # traceFiles.setdefault(hosts[1], []).append(fileName)

    return bgTrafficSrv


def startHTTPTraffic(exp, webSrv, webClts, httpRate, traceFiles):
    '''
    Start HTTP taffic using web polygraph
    '''

    logger.info('')
    logger.info('+++++ startHTTPTraffic +++++')
    # Start web polygraph server
    webSrvIP = exp.get_node(webSrv).IP()
    logger.debug('Start polygraph-server on %s' % webSrvIP)
    webSrvF = genPolygraphFile( homeDir+'simple.pg', webSrvIP)
    exp.node_to_worker[webSrv].put_file(webSrvF, '/tmp/')
    exp.get_node(webSrv).cmd('polygraph-server --config %s --verb_lvl 10 --console /tmp/pg-server-console.out \
        --stats_cycle 1sec & echo $! > /tmp/poly-srv.pid;' % (webSrvF))
    traceFiles.setdefault(webSrv, []).append('/tmp/pg-server-console.out')

    # Start web polygraph clients
    for i in range(len(webClts)):
        webCltIP = exp.get_node(webClts[i]).IP()
        webCltF = genPolygraphFile( homeDir+'simple.pg', webSrvIP, webCltIP, httpRate)
        exp.node_to_worker[webClts[i]].put_file(webCltF, '/tmp/')
        logger.debug('Start polygraph-client on %s' % webCltIP)
        fileName = '/tmp/pg-client-console-%s.out' % webClts[i]
        exp.get_node(webClts[i]).cmd('polygraph-client --config %s --verb_lvl 10 --console %s \
            --stats_cycle 1sec & echo $! > /tmp/poly-clt-%s.pid;' % (webCltF, fileName, webClts[i]))
        traceFiles.setdefault(webClts[i], []).append(fileName)


def startAttackTraffic(exp, attackPairs, bw, attackLen, traceFiles):
    '''
    Start UDP attack traffic with iperf
    '''

    logger.info('')
    logger.info('+++++ startAttackTraffic +++++')
    pktSize = 1250
    pktInt = int(10**6 * pktSize * 8 / (bw * 10**6)) # bw in Mbps
    attackSrvStarted = []

    for i in range(len(attackPairs)):
        attackClt, attackSrv = attackPairs[i][0], attackPairs[i][1]
        logger.debug('Start iperf: %s => %s' % (attackClt, attackSrv))
        if False: # TCP attack traffic
            if attackSrv not in attackSrvStarted:
                fileName = '/tmp/iperf-attack-tcp-server-%s.out' % (attackSrv)
                exp.get_node(attackSrv).cmd('iperf -s -i 1 > %s &' % (fileName))
                traceFiles.setdefault(attackSrv, []).append(fileName)
            exp.get_node(attackClt).cmd('iperf -c %s -t %d -l 1250 -i 1 &' % (exp.get_node(attackSrv).IP(), attackLen))
        else:
            # if attackSrv not in attackSrvStarted:
            #     fileName = '/tmp/iperf-attack-udp-server-%s.out' % (attackSrv)
            #     exp.get_node(attackSrv).cmd('iperf -s -u -i 1 > %s &' % (fileName))
            #     traceFiles.setdefault(attackSrv, []).append(fileName)
            # exp.get_node(attackClt).cmd('iperf -c %s -u -t %d -l 1250 -b %dm -i 1 &' % \
            #     (exp.get_node(attackSrv).IP(), attackLen, 2*bw)) #

            fileName = '/tmp/hping3-attack-udp-client-%s.out' % attackClt
            # cmdHping3 = 'sudo hping3 %s --quiet --data 1250 --interval u%d --udp --ttl 2 1>/dev/null 2>%s &' \
            #     % (exp.get_node(attackSrv).IP(), pktInt, fileName)
            cmdHping3 = 'sudo hping3 %s --quiet --data 1250 --interval u%d --udp 1>/dev/null 2>%s &' \
                % (exp.get_node(attackSrv).IP(), pktInt, fileName)

            cmdKill = 'echo "sleep %d; sudo pkill hping3;" > kill-hping3-attack.sh; bash kill-hping3-attack.sh &' % (attackLen)
            exp.get_node(attackClt).cmd(cmdHping3, shell=True)
            exp.get_node(attackClt).cmd(cmdKill, shell=True)
            # "sudo hping3 -2 -q -p 8889 -i u$INT -d 64 ${UDP_VMs[0]} 1>/dev/null 2>hping3.stat & sleep $RunTime; sudo pkill hping3;"
            traceFiles.setdefault(attackClt, []).append(fileName)
            logger.debug('- %s', attackClt)
            logger.debug('  - %s',cmdHping3)

        attackSrvStarted.append(attackSrv)

    return attackSrvStarted


def stopDDoS(exp, topo, webSrv, webClts, traceFiles, mapAlg, swIntfs, bw=10):
    '''
    Stop experiment, kill processes, retrive tace files
    '''

    logger.info('')
    logger.info('+++++ stopDDoS +++++')
    timeStamp = time.strftime('%y_%m_%d-%H_%M_%S', time.gmtime())
    folder = 'ddos-rf%d-%dMB-%s-%dPM-%s/' % (len(topo.switches()), bw, mapAlg, \
        len(exp.cluster.workers()), timeStamp)
    subprocess.check_output(['mkdir', '-p', folder])
    parsedLog = open(folder+'parsed-intfs-cpu.log', 'w')

    if webSrv:
        logger.debug('Stopping web polygraph ...')
        exp.get_node(webSrv).cmd('sudo kill -2 `cat /tmp/poly-srv.pid`;')
        # exp.node_to_worker[webSrv].get_file('/tmp/pg-server-console.out', folder)
        for i in range(len(webClts)):
            exp.get_node(webClts[i]).cmd('sudo kill -2 `cat /tmp/poly-clt-%s.pid`;' % (webClts[i]))
            # exp.node_to_worker[webClts[i]].get_file('/tmp/pg-client-console-%s.out' % (webClts[i]), folder)

    # if bgTrafficSrv:
    #     for srv in bgTrafficSrv:
    #         exp.node_to_worker[srv].get_file('/tmp/iperf-bg-tcp-server-%s.out' % (srv), folder)

    # if attackRcv:
    #     for rcv in attackRcv:
    #         exp.node_to_worker[rcv].get_file('/tmp/iperf-attack-udp-server-%s.out' % (rcv), folder)

    logger.debug('Getting trace files ...')
    for h in traceFiles:
        for tf in traceFiles[h]:
            exp.node_to_worker[h].get_file(tf, folder)

    for worker in exp.cluster.workers():
        wName = worker.hn()
        bwmTrace = 'bwm-out-%s.log' % (wName)
        cpuTrace = 'maxinet_cpu_%d_(%s).log' % (exp.hostname_to_workerid[wName], wName)
    #     # traces[wName] = [bwmTrace, cpuTrace]
        worker.run_cmd('sudo pkill bwm-ng')
        # worker.run_cmd('sudo pkill hping3')
        worker.get_file('/tmp/'+bwmTrace, folder)
        worker.get_file('/tmp/'+cpuTrace, folder)
        # parsedLog.write('%s\n' % wName)
        parseTrace(wName, folder+bwmTrace, folder+cpuTrace.replace('(','\(').replace(')','\)'), parsedLog, swIntfs[wName]+['total', 'em1']) # swIntfs[wName]+

    parsedLog.close()

    return folder

# def runDDoS_md(mapAlg='METIS'):
#     # thrput = 10
#     # rate = 10000/thrput
#     httpLen = 60
#     attackLen = 60
#     bw = 10
#     httpRate = 200
#     testFlowRules = False
#     # mapAlg = 'UC-MKL'
#     # mapAlg = 'US-METIS'
#     # mapAlg = 'METIS'
#     traceFiles = {}   # {node1: file_name1[,node2: file_name2, ...]}


#     logger.info('+++++ %s mapping algorithm +++++', mapAlg)
#     ### Generate Mininet topo object
#     t = TopoSet(36, typeTopo='rocketfuel', bw=bw)
#     t.genTopo()
#     topo = t.getTopoWKey()['rocketfuel'][0]

#     ### Add edge hosts
#     addEdgeHosts(topo, bw, 3)
    
#     checkTopo(topo)
#     ### Find a switch for web server to attach
#     assignWebSw(topo)
#     webSw = 's1' # assignWebSw(topo)
#     webSrv = webSw.replace('s','h')

#     ### Assign edge hosts as attack clients and web clients
#     [attackPairs, webClts] = assignAttackerVictim(topo, webSw)
#     logger.info('WebClients: [%s] => %s' % (' '.join(webClts), webSrv))
#     logger.info('Attackers: %s' % attackPairs)

#     ### Add host for each switch (used for background TCP traffic)
#     addHosts(topo, topo.switches(), bw)

#     ### Update path to web server host
#     pathsToWebSrv = computePath(topo, webSrv) 

#     ### Compute paths from attack clients to attack receivers
#     pathsAttack = {}
#     for p in attackPairs:
#         pathsAttack[p[1]] = computePath(topo, p[1])

#     ### Start MaxiNet experiment
#     cluster = maxinet.Cluster(minWorkers=3, maxWorkers=3)
#     if mapAlg == 'METIS':
#         exp = maxinet.Experiment(cluster, topo)
#     else:
#         mapping = partitionTopo(topo, PMCap, PMIdx, mapAlg)
#         exp = maxinet.Experiment(cluster, topo, nodemapping=mapping) #, , , nodemapping=mapping
    
#     exp.setup()
#     exp.monitor()

#     ### Install flow rules for web traffic
#     pathsToTest = []
#     for h in webClts:
#         pathsToTest.append(pathsToWebSrv[h])
#         addPathFlowRules(topo, exp, pathsToWebSrv[h])

#     ### Install flow rules for attack traffic
#     for p in attackPairs:
#         # pathsToTest.append(pathsAttack[p[1]][p[0]])
#         addPathFlowRules(topo, exp, pathsAttack[p[1]][p[0]])

#     ### Test flow rules
#     if testFlowRules:
#         logger.info('Testing path connectivity ...')
#         for p in pathsToTest:
#             testPathFlowRules(exp, p)

#     ### Install and test flow rules for background TCP traffic
#     # SwHLinks = addLocalFlowRules(topo, exp)
#     addLocalBCRules(topo, exp)
#     if testFlowRules:
#         testLocalFlowRules(topo, SwHLinks, exp)

#     # exp.CLI(locals(), globals())

#     # time.sleep(10)

#     # ### Start bwm-ng for throughput monitoring ###
#     swIntfs = startBwm(exp)

#     # ### Start background TCP traffic
#     # ### Start iperf server on all hosts
#     # bgTrafficSrv = startBGTraffic(topo, exp, pathsToTest, bw, httpLen+attackLen, traceFiles)
#     # bgTrafficSrv = startBGTraffic(topo, exp, None, bw, httpLen+attackLen, traceFiles)
#     startBCTraffic(topo, exp, None, bw, httpLen+attackLen, traceFiles)

#     # ### Start web polygraph
#     startHTTPTraffic(exp, webSrv, webClts, httpRate, traceFiles)

#     # ### Run with background and http traffic
#     time.sleep(httpLen)

#     # ### Start attack traffic 
#     attackRcv = startAttackTraffic(exp, attackPairs, bw, attackLen, traceFiles)

#     # ### Run with attack traffic
#     time.sleep(attackLen)

#     # # Kill polygraph webSrv and webClts, bwm-ng
#     # # Fetch trace and log files
#     stopDDoS(exp, webSrv, webClts, None, attackRcv, traceFiles, mapAlg, swIntfs)
#     # stopDDoS(exp, None, None, None, None, traceFiles, mapAlg, swIntfs)

#     logger.info('')
#     logger.info('+++++++++++++++ Completed +++++++++++++++')
#     logger.info('+++++++++++++++++++++++++++++++++++++++++')
#     exp.stop()


# if __name__ == '__main__':

#     runDDoS_md(sys.argv[1].upper())