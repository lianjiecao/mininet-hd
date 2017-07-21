#! /usr/bin/python2.7

import os, sys, time, logging
# import termcolor as T
import argparse, subprocess

# from mininet.cli import CLI
# from mininet.topo import Topo, LinearTopo
# from mininet.net import Mininet
# from mininet.node import UserSwitch, OVSSwitch, IVSSwitch, RemoteController, CPULimitedHost
# from mininet.link import TCLink

from MaxiNet.Frontend import maxinet

# from dijkstra import DGraph, dijsktraCompute
import ddosLib as ddos
sys.path.append('/home/cao/mininet-hd/simulator')
from topoSet import TopoSet
# from partitioner import MetisPartitioner, ChacoUEPartitioner, MininetPartitioner
# import simulatorFunc

# Original:
# 2core@1.20GHz:[ 0.00647285  3.76108616  0.60448344]
# 2core@1.86GHz:[  0.01610504   4.7397206  -10.65534441]
# 2core@2.39GHz:[  0.02926232   5.38848162 -21.01192069]
# 4core@2.39GHz:[  0.03530996  14.79035224  -1.57579898]
# 4core@1.86GHz:[  0.06338502   9.15789972  11.68651059]
# 4core@1.20GHz:[  0.05784107   5.40452558  35.90295853]

# Mod: 0.85@7sw
# 2core@1.20GHz:[  0.000795402690   3.99206024  -2.94350357]
# 2core@1.86GHz:[  0.00848321306   5.04957094  -15.3294361]
# 2core@2.39GHz:[  0.0179109944   5.89216706  -27.8967675]
# 4core@2.39GHz:[  0.04608418  13.16127104   9.49318331]
# 4core@1.86GHz:[  0.07551359   7.44974746  27.07816148]
# 4core@1.20GHz:[  0.05965218   4.66032584  41.88254841]

# cap31
#   4 core @ 2.39 GHz.
# cap32
#   4 core @ 1.33 GHz.
# cap33
#   2 core @ 2.39 GHz.
# cap34
#   4 core @ 2.39 GHz.
# cap35
#   2 core @ 2.39 GHz.
# cap36
#   2 core @ 1.33 GHz.

# # 2core@1.20GHz
# 190     0       180     -2.94350357e+00, 1.99603012e+00, 1.98850672e-04
# # 2core@1.86GHz
# 190     0       180     -1.53294361e+01, 2.52478547e+00, 2.12080327e-03
# # 2core@2.39GHz
# 190     0       180     -2.78967675e+01, 2.94608353e+00, 4.47774860e-03
# # 4core@1.20GHz
# 390     0       360     4.18825484e+01, 1.16508146e+00, 3.72826105e-03
# # 4core@1.86GHz
# 390     0       360     2.70781615e+01, 1.86243686e+00, 4.71959954e-03
# # 4core@2.39GHz
# 390     0       360     9.49318331e+00, 3.29031776e+00, 2.88026139e-03


# Max capacity: {'cap34':1400, 'cap35':800, 'cap36':500}
# PMCap = {'cap34':1120, 'cap35':640, 'cap36':440}
# PMInfo = {
#     # PM_NAME:[PM_IDX, MAX_CPU_SHARE, MIN_SWITCH_CPU_SHARE, [pm_cap_func]]
#     'cap31':[3, 360, 0, 320, [2.88026139e-03, 3.29031776e+00, 9.49318331e+00]],
#     'cap32':[4, 360, 0, 320, [3.72826105e-03, 1.16508146e+00, 4.18825484e+01]],
#     'cap33':[5, 180, 0, 160, [4.47774860e-03, 2.94608353e+00, -2.78967675e+01]],
#     'cap34':[0, 360, 0, 320, [2.88026139e-03, 3.29031776e+00, 9.49318331e+00]], 
#     'cap35':[1, 180, 0, 160, [4.47774860e-03, 2.94608353e+00, -2.78967675e+01]],
#     'cap36':[2, 180, 0, 160, [1.98850672e-04, 1.99603012e+00, -2.94350357e+00]],
# }
PMInfo = {
    'cap31':[3, 2, 360, 0, 320, [9.49318331, 3.29031776, 0.00288026139]],
    'cap32':[4, 2, 360, 0, 320, [41.8825484, 1.16508146, 0.00372826105]],
    'cap33':[5, 1, 180, 0, 160, [-27.8967675, 2.94608353, 0.00447774860]],
    'cap34':[0, 2, 360, 0, 320, [9.49318331, 3.29031776, 0.00288026139]],
    'cap35':[1, 1, 180, 0, 160, [-27.8967675, 2.94608353, 0.00447774860]],
    'cap36':[2, 1, 180, 0, 160, [-2.94350357, 1.99603012, 0.000198850672]],
}

# PMIdx = {'cap34':0, 'cap35':1, 'cap36':2, 'cap31':3, 'cap32':4, 'cap33':5}
# CPUInfo = {
#     'cap31':[3, 360, 0, 320, [400]],
#     'cap32':[4, 360, 0, 320, [400]],
#     'cap33':[5, 180, 0, 160, [200]],
#     'cap34':[0, 360, 0, 320, [400]], 
#     'cap35':[1, 180, 0, 160, [200]],
#     'cap36':[2, 180, 0, 160, [200]],
# }

CPUInfo = {
    'cap31':[3, 360, 0, 320, [400*2.39]],
    'cap32':[4, 360, 0, 320, [400*1.33]],
    'cap33':[5, 180, 0, 160, [200*2.39]],
    'cap34':[0, 360, 0, 320, [400*2.39]],
    'cap35':[1, 180, 0, 160, [200*2.39]],
    'cap36':[2, 180, 0, 160, [200*1.33]],
}


def runDDoS_md(mapAlg='METIS', numPM=None):
    logLevel = logging.DEBUG
    # logLevel = logging.INFO
    logger = logging.getLogger('ddos-md')
    logger.setLevel(logLevel)
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)-5s:%(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate = False

    # thrput = 10
    # rate = 10000/thrput
    httpLen = 60
    attackLen = 60
    bw = 16
    httpRate = 200
    testFlowRules = False
    # mapAlg = 'UC-MKL'
    # mapAlg = 'US-METIS'
    # mapAlg = 'METIS'
    traceFiles = {}   # {node1: file_name1[,node2: file_name2, ...]}


    logger.info('+++++ %s mapping algorithm +++++', mapAlg)
    ### Generate Mininet topo object ###
    t = TopoSet(36, typeTopo='rocketfuel', bw=bw)
    t.genTopo()
    topo = t.getTopoWKey()['rocketfuel'][0]
    print topo.hosts()

    ### Add edge hosts ###
    ddos.addEdgeHosts(topo, 2*bw, 3)
    
    ddos.checkTopo(topo)
    ### Find a switch for web server to attach ###
    # candidates: ('s29', 9) ('s3', 8) ('s7', 8) ('s5', 8) ('s10', 8) ('s1', 7) ('s32', 7) ('s22', 7)
    ddos.assignWebSw(topo)
    webSw = 's1' # 's10' # 's32' # 's1' 
    webSrv = webSw.replace('s','h')

    ### Assign edge hosts as attack clients and web clients ###
    [attackPairs, webClts] = ddos.assignAttackerVictim(topo, webSw)
    logger.info('WebClients: [%s] => %s' % (' '.join(webClts), webSrv))
    logger.info('Attackers: %s' % attackPairs)

    ### Add host for each switch (used for background TCP traffic) ###
    ddos.addHosts(topo, topo.switches(), 2*bw)

    ### Update path to web server host ###
    pathsToWebSrv = ddos.computePath(topo, webSrv) 

    ### Compute paths from attack clients to servers ###
    pathsAttack = {}
    for p in attackPairs:
        pathsAttack[p[1]] = ddos.computePath(topo, p[1])

    ### Start MaxiNet experiment ###
    cluster = maxinet.Cluster(minWorkers=6, maxWorkers=6)
    if mapAlg == 'METIS':
        exp = maxinet.Experiment(cluster, topo)
    # elif mapAlg == 'US-METIS':
    #     if numPM:
    #         numPM = numPM if numPM <= len(CPUInfo) else len(CPUInfo)
    #     mapping = ddos.partitionTopo(topo, CPUInfo, mapAlg)
    #     exp = maxinet.Experiment(cluster, topo, nodemapping=mapping)
    else:
        mapping = ddos.partitionTopo(topo, PMInfo, mapAlg)
        exp = maxinet.Experiment(cluster, topo, nodemapping=mapping) #, , , nodemapping=mapping
    
    exp.setup()
    exp.monitor()

    ### Install flow rules for web traffic ###
    pathsToTest = []
    for h in webClts:
        pathsToTest.append(pathsToWebSrv[h])
        intfsOnWebPaths = ddos.addPathFlowRules(topo, exp, pathsToWebSrv[h])
        print intfsOnWebPaths

    ### Install flow rules for attack traffic ###
    for p in attackPairs:
        # pathsToTest.append(pathsAttack[p[1]][p[0]])
        ddos.addPathFlowRules(topo, exp, pathsAttack[p[1]][p[0]])

    ### Test flow rules ###
    if testFlowRules:
        logger.info('Testing path connectivity ...')
        for p in pathsToTest:
            ddos.testPathFlowRules(exp, p)

    ### Install and test flow rules for background TCP traffic ###
    # SwHLinks = addLocalFlowRules(topo, exp)
    # if testFlowRules:
    #     ddos.testLocalFlowRules(topo, SwHLinks, exp)
    ddos.addLocalBCRules(topo, exp)

    # exp.CLI(locals(), globals())

    # time.sleep(10)
    print exp.get_node(webClts[0]).cmd('ping -c 3 %s' % (exp.get_node(webSrv).IP()))

    ### Start bwm-ng for throughput monitoring ###
    swIntfs = ddos.startBwm(topo, exp)

    ### Start background TCP traffic ###
    ### Start iperf server on all hosts ###
    # ddos.bgTrafficSrv = startBGTraffic(topo, exp, pathsToTest, bw, httpLen+attackLen, traceFiles)
    # ddos.bgTrafficSrv = startBGTraffic(topo, exp, None, bw, httpLen+attackLen, traceFiles)

    ### Start background UDP broadcast traffic using hping3 ###
    # ddos.startBCTraffic(topo, exp, pathsToTest, bw, httpLen+attackLen, traceFiles)
    ddos.startBCTraffic(topo, exp, None, bw, httpLen+attackLen, traceFiles)

    # ### Start web polygraph ###
    ddos.startHTTPTraffic(exp, webSrv, webClts, httpRate, traceFiles)

    ### Run with background and http traffic ###
    time.sleep(httpLen)

    ### Start attack traffic ###
    attackRcv = ddos.startAttackTraffic(exp, attackPairs, bw, attackLen, traceFiles)

    ### Run with attack traffic ###
    time.sleep(attackLen)

    ### Kill polygraph webSrv and webClts, bwm-ng ###
    ### Fetch trace and log files ###
    logFolder = ddos.stopDDoS(exp, topo, webSrv, webClts, traceFiles, mapAlg, swIntfs, bw)
    # ddos.stopDDoS(exp, None, None, traceFiles, mapAlg, swIntfs)

    logger.info('')
    logger.info('Leaving log and trace folder: %s', logFolder)
    logger.info('+++++++++++++++ Completed +++++++++++++++')
    logger.info('+++++++++++++++++++++++++++++++++++++++++')
    exp.stop()


def runDDoS_sm(mapAlg='METIS', numPM=None):

    logLevel = logging.DEBUG
    # logLevel = logging.INFO
    logger = logging.getLogger('ddos-sm')
    logger.setLevel(logLevel)
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)-5s:%(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate = False


    # thrput = 10
    # rate = 10000/thrput
    httpLen = 60
    attackLen = 60
    bw = 60
    httpRate = 100
    testFlowRules = False
    # mapAlg = 'UC-MKL'
    # mapAlg = 'US-METIS'
    # mapAlg = 'METIS'
    traceFiles = {}   # {node1: file_name1[,node2: file_name2, ...]}


    logger.info('+++++ %s mapping algorithm +++++', mapAlg)
    ### Generate Mininet topo object ###
    t = TopoSet(11, typeTopo='rocketfuel', bw=bw)
    t.genTopo()
    topo = t.getTopoWKey()['rocketfuel'][0]

    ### Add edge hosts ###
    # ddos.addEdgeHosts(topo, bw, 3)

    ### Add host for each switch (used for background traffic) ###
    ddos.addHosts(topo, topo.switches(), 2*bw)
    
    ddos.checkTopo(topo)
    ### Find a switch for web server to attach ###
    ddos.assignWebSw(topo)
    webSw = 's1' # assignWebSw(topo)
    webSrv = webSw.replace('s','h')

    ### Assign edge hosts as attack clients and web clients ###
    # [attackPairs, webClts] = ddos.assignAttackerVictim(topo, webSw)

    ### Manually assign edge hosts as attack clients and web clients ###
    webClts = ['h3', 'h5']
    attackPairs = [('h6', 'h8'),('h7', 'h2')]

    logger.info('WebClients: [%s] => %s' % (' '.join(webClts), webSrv))
    logger.info('Attackers: %s' % attackPairs)

    ### Update path to web server host ###
    pathsToWebSrv = ddos.computePath(topo, webSrv) 

    ### Compute paths from attack clients to attack receivers ###
    pathsAttack = {}
    for p in attackPairs:
        pathsAttack[p[1]] = ddos.computePath(topo, p[1])

    ### Start MaxiNet experiment ###
    cluster = maxinet.Cluster(minWorkers=6, maxWorkers=6)
    if mapAlg == 'METIS':
        exp = maxinet.Experiment(cluster, topo)
    elif mapAlg == 'OVER-PROV':
        mapping = {
            's5':0, 'h5':0, 's7':0, 'h7':0, 's4':0, 'h4':0,  \
            's10':3, 'h10':3, 's6':3, 'h6':3, 's3':3, 'h3':3, \
            's11':4, 'h11':4, 's2':4, 'h2':4, \
            's9':5, 'h9':5, 's8':5, 'h8':5, \
            's1':1, 'h1':1, 
        }
        exp = maxinet.Experiment(cluster, topo, nodemapping=mapping)
    # elif mapAlg == 'US-METIS':
    #     mapping = ddos.partitionTopo(topo, CPUInfo, mapAlg)
    #     exp = maxinet.Experiment(cluster, topo, nodemapping=mapping)
    else:
        mapping = ddos.partitionTopo(topo, PMInfo, mapAlg)
        exp = maxinet.Experiment(cluster, topo, nodemapping=mapping) #, , , nodemapping=mapping
    
    exp.setup()
    exp.monitor()

    ### Install flow rules for web traffic ###
    pathsToTest = []
    for h in webClts:
        if testFlowRules:
            pathsToTest.append(pathsToWebSrv[h])
        ddos.addPathFlowRules(topo, exp, pathsToWebSrv[h])

    ### Install flow rules for attack traffic ###
    for p in attackPairs:
        if testFlowRules:
            pathsToTest.append(pathsAttack[p[1]][p[0]])
        ddos.addPathFlowRules(topo, exp, pathsAttack[p[1]][p[0]])

    ### Test flow rules ###
    if testFlowRules:
        logger.info('Testing path connectivity ...')
        for p in pathsToTest:
            ddos.testPathFlowRules(exp, p)

    ### Install and test flow rules for background TCP traffic ###
    # SwHLinks = addLocalFlowRules(topo, exp)
    # if testFlowRules:
    #     ddos.testLocalFlowRules(topo, SwHLinks, exp)
    ddos.addLocalBCRules(topo, exp)

    # exp.CLI(locals(), globals())

    # time.sleep(10)
    print exp.get_node(webClts[0]).cmd('ping -c 3 %s' % (exp.get_node(webSrv).IP()))

    ### Start bwm-ng for throughput monitoring ###
    swIntfs = ddos.startBwm(topo, exp)

    ### Start background TCP traffic ###
    ### Start iperf server on all hosts ###
    # ddos.bgTrafficSrv = startBGTraffic(topo, exp, pathsToTest, bw, httpLen+attackLen, traceFiles)
    # ddos.bgTrafficSrv = startBGTraffic(topo, exp, None, bw, httpLen+attackLen, traceFiles)

    ### Start background UDP broadcast traffic using hping3 ###
    # ddos.startBCTraffic(topo, exp, pathsToTest, bw, httpLen+attackLen, traceFiles)

    ### Start broadcast UDP traffic ###
    ddos.startBCTraffic(topo, exp, None, bw, httpLen+attackLen, traceFiles)

    # ### Start web polygraph ###
    ddos.startHTTPTraffic(exp, webSrv, webClts, httpRate, traceFiles)

    ### Run with background and http traffic ###
    time.sleep(httpLen)

    ### Start attack traffic ###
    attackRcv = ddos.startAttackTraffic(exp, attackPairs, bw, attackLen, traceFiles)

    ### Run with attack traffic ###
    time.sleep(attackLen)

    ### Kill polygraph webSrv and webClts, bwm-ng ###
    ### Fetch trace and log files ###
    logFolder = ddos.stopDDoS(exp, topo, webSrv, webClts, traceFiles, mapAlg, swIntfs, bw)
    # logFolder = ddos.stopDDoS(exp, None, None, traceFiles, mapAlg, swIntfs)

    logger.info('')
    logger.info('Leaving log and trace folder: %s', logFolder)
    logger.info('+++++++++++++++ Completed +++++++++++++++')
    logger.info('+++++++++++++++++++++++++++++++++++++++++')
    exp.stop()



def testMapAlg(mapAlg='METIS'):
    bw = 25
    traceFiles = {}   # {node1: file_name1[,node2: file_name2, ...]}


    # print '+++++ %s mapping algorithm +++++' % mapAlg
    # ### Generate Mininet topo object ###
    # t = TopoSet(36, typeTopo='rocketfuel', bw=bw)
    # t.genTopo()
    # topo = t.getTopoWKey()['rocketfuel'][0]

    # ### Add edge hosts ###
    # # ddos.addEdgeHosts(topo, bw, 3)

    # ### Add host for each switch (used for background TCP traffic) ###
    # # ddos.addHosts(topo, topo.switches(), 2*bw)
    # ddos.addEdgeHosts(topo, 2*bw, 3)
    
    # ddos.checkTopo(topo)
    # ### Find a switch for web server to attach ###
    # for h in topo.hosts():
    #     print topo.nodeInfo(h)

    # mapping = ddos.partitionTopo(topo, PMCapF, PMIdx, mapAlg)

    cluster = maxinet.Cluster(minWorkers=6, maxWorkers=6)
    for w in cluster.workers():
        print w.hn()


def main():

    parser = argparse.ArgumentParser(description="Parse DDoS experiment results")

    parser.add_argument('--algorithm',
                        dest="alg",
                        action="store",
                        help="Partitioning algorithm: wf, c90",
                        default='METIS',
                        )

    parser.add_argument('--ddos-size',
                        dest="ddos",
                        action="store",
                        help="Size of DDoS experiment: sm, md",
                        default='small',
                        )

    parser.add_argument('--numPM',
                        dest="numPM",
                        action="store",
                        help="Number of PM to use",
                        default=None,
                        )

    args = parser.parse_args()

    if args.ddos == 'small' or args.ddos == 'sm':
        runDDoS_sm(mapAlg=args.alg.upper(), numPM=args.numPM)
    elif args.ddos == 'medium' or args.ddos == 'md':
        runDDoS_md(mapAlg=args.alg.upper(), numPM=args.numPM)


if __name__ == '__main__':
    main()
