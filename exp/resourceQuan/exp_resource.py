#!/usr/bin/python2

#
# Minimal example showing how to use MaxiNet with static mapping of nodes to workers
#

from time import sleep
import subprocess, sys, logging, argparse

from MaxiNet.Frontend import maxinet
from MaxiNet.tools import FatTree, LinearTopo

#from mininet.topo import Topo, LinearTopo
from mininet.util import custom, irange
from mininet.node import UserSwitch, OVSSwitch, IVSSwitch, RemoteController, CPULimitedHost
from mininet.topo import Topo

# logLevel = logging.DEBUG
logLevel = logging.INFO
logger = logging.getLogger('res-quan')
logger.setLevel(logLevel)
ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-5s:%(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.propagate = False




# def setCPUFreq(pm, nCore, freq):

#     for c in range(nCore):
#         # ssh cap32 'sudo cpufreq-set -c 0 -f $s'
#         subprocess.check_output('ssh %s 'sudo cpufreq-set -c %d -f %s'' % (pm, c, freq), shell=True)

#     return

def parseTrace(bwmTrace, cpuTrace, outputFile, intf='total'):
    # Type rate:
    # unix timestamp;iface_name;bytes_out/s;bytes_in/s;bytes_total/s;bytes_in;bytes_out;packets_out/s;packets_in/s;
    # packets_total/s;packets_in;packets_out;errors_out/s;errors_in/s;errors_in;errors_out\n

    bwmCont = subprocess.check_output('grep %s %s' % (intf, bwmTrace), shell=True).split('\n')
    rates = {'tx':[], 'rx':[], 'pkt_out':[], 'pkt_in':[]}
    startTime, endTime = int(bwmCont[10].split(';')[0]), int(bwmCont[-10].split(';')[0])
    for line in bwmCont[5:-5]:
        tokens = line.split(';')
        rates['tx'].append(round(float(tokens[2])*8/1000000))
        rates['rx'].append(round(float(tokens[3])*8/1000000))
        rates['pkt_out'].append(round(float(tokens[7])))
        rates['pkt_in'].append(round(float(tokens[8])))

    # cpuCont = subprocess.check_output('grep -A %d %d %s | awk '{print $13}'' % \
    #     (endTime-startTime, startTime, cpuTrace), shell=True).split('\n')
    cpuCont = subprocess.check_output("grep -A %d %d %s | awk '{print $13}'" % \
        (endTime-startTime, startTime, cpuTrace), shell=True).split('\n')
    cpuUtils = [100-float(x) for x in cpuCont[:-1]]

    if outputFile:
        # More readable output
        # outputFile.write('  %s:tx %d \n  %s:rx %d \n  %s:pkt_out %d \n  %s:pkt_in %d \n  cpu %d \n' % (
        #     intf, sum(rates['tx'])/len(rates['tx']), intf, sum(rates['rx'])/len(rates['rx']), 
        #     intf, sum(rates['pkt_out'])/len(rates['pkt_out']), intf, sum(rates['pkt_in'])/len(rates['pkt_in']),
        #     round(sum(cpuUtils)/len(cpuUtils))))

        # More parsable output
        # tx rx pkt_out pkt_in cpu
        outputFile.write('%d %d %d %d %d\n' % (
            sum(rates['tx'])/len(rates['tx']), sum(rates['rx'])/len(rates['rx']), 
            sum(rates['pkt_out'])/len(rates['pkt_out']), sum(rates['pkt_in'])/len(rates['pkt_in']),
            round(sum(cpuUtils)/len(cpuUtils))))
    else:
        print intf+':tx', sum(rates['tx'])/len(rates['tx'])
        print intf+':rx', sum(rates['rx'])/len(rates['rx'])
        print intf+':pkt_out', sum(rates['pkt_out'])/len(rates['pkt_out'])
        print intf+':pkt_in', sum(rates['pkt_in'])/len(rates['pkt_in'])
        print 'cpu', round(sum(cpuUtils)/len(cpuUtils))


def csvToDict(csvFile, sep=','):
    '''
    Read a csv file (first line as keywords) and return a dictionary
    '''
    info = {}
    keyMap = {}
    cont = open(csvFile, 'r').read().strip()
    lines = cont.split('\n')
    keywords = lines[0].split(sep)
    for i in range(len(keywords)):
        keyMap[i] = keywords[i]
        info[keywords[i]] = []
    for i in range(1, len(lines)):
        tokens = lines[i].split(sep)
        for j in range(len(tokens)):
            info[keyMap[j]].append(toFloat(tokens[j]))
    return info

def toFloat(s):
    try:
        return float(s)
    except ValueError:
        return s

def parseResmonTraces(resourceTrace, nicTraces, outputFile, intf='total'):
    '''
    Parse trace files of python-resmon
    '''
    ### resourceTrace format ###
    # Timestamp,  Uptime, NCPU, %CPU, %CPU0, %CPU1, %CPU2, %CPU3, %MEM, mem.total.KB, mem.used.KB, mem.avail.KB, mem.free.KB, 
    # %SWAP, swap.total.KB, swap.used.KB, swap.free.KB, io.read, io.write, io.read.KB, io.write.KB, io.read.ms, io.write.ms

    ### nicTraces format ###
    # Timestamp,  Uptime, NIC, sent.B, recv.B, sent.pkts, recv.pkts, err.in, err.out, drop.in, drop.out

    specialKeywords = ['Timestamp', 'NIC']
    nicTracesSelected = []
    nicInfo = {}
    if intf == 'total':
        nicTracesSelected = nicTraces
    else:
        for f in nicTraces:
            if intf in f:
                nicTracesSelected.append(f)
    nicInfoTmp = [csvToDict(f, sep=', ') for f in nicTracesSelected] # List of dictionaries
    if len(nicInfoTmp) > 1:
        keywords = nicInfoTmp[0].keys()
        for k in specialKeywords:
            keywords.remove(k)
        for k in keywords:
            nicInfo[k] = addLists([x[k] for x in nicInfoTmp])
    else:
        nicInfo = nicInfoTmp[0]

    resInfo = csvToDict(resourceTrace, sep=', ')

    cpu = round(sum(resInfo['%CPU'][10:-10])/len(resInfo['%CPU'][10:-10]))
    txMbps = round(sum(nicInfo['sent.B'][10:-10])/len(nicInfo['sent.B'][10:-10])*8/1000000)
    rxMbps = round(sum(nicInfo['recv.B'][10:-10])/len(nicInfo['recv.B'][10:-10])*8/1000000)
    txpps = round(sum(nicInfo['sent.pkts'][10:-10])/len(nicInfo['sent.pkts'][10:-10]))
    rxpps = round(sum(nicInfo['recv.pkts'][10:-10])/len(nicInfo['recv.pkts'][10:-10]))

    if outputFile:
        outputFile.write('%d %d %d %d %d\n' % (txMbps, rxMbps, txpps, rxpps, cpu))
    else:
        print intf+':tx', txMbps
        print intf+':rx', rxMbps
        print intf+':pkt_out', txpps
        print intf+':pkt_in', rxpps
        print 'cpu', cpu


def addLists(lists):
    '''
    Take 2D array, return 1D array
    '''
    listSum = []
    for i in range(len(lists[0])):
        listSum.append(toSum([x[i] for x in lists]))
    return listSum


def toSum(nums):
    try:
        return sum(nums)
    except:
        return nums[0]

def addPathFlowRules(topo, exp, path):
    '''
    Install rules to all switches on a path
    '''

    logger.info('')
    logger.info('+++++ addPathFlowRules +++++')
    logger.info('Install rules for path: %s', ' => '.join(path))
    nodeWPorts = {}
    tunnels = [sorted([x[0], x[1]]) for x in exp.topology.getTunnels()]

    # Find in and out ports on the same switch
    for i in range(0, len(path)-1):
        origPorts = topo.port(path[i], path[i+1])
        if sorted([path[i], path[i+1]]) in tunnels:
            intf1 = intf2 = exp.tunnellookup[(path[i], path[i+1])]
        else:
            intf1, intf2 = '%s-eth%d' % (path[i], origPorts[0]), '%s-eth%d' % (path[i+1], origPorts[1])
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



# class MyLinearTopo( Topo ):
#     'Linear topology of k switches, with n hosts per switch.'

#     def build( self, k=2, n=1, **_opts):
#         '''k: number of switches
#            n: number of hosts per switch'''
#         self.k = k
#         self.n = n

#         if n == 1:
#             genHostName = lambda i, j: 'h%s' % i
#         else:
#             genHostName = lambda i, j: 'h%ss%d' % ( j, i )

#         lastSwitch = None
#         for i in irange( 1, k ):
#             # Add switch
#             switch = self.addSwitch( 's%s' % i )
#             # Add hosts to switch
#             for j in irange( 1, n ):
#                 host = self.addHost( genHostName( i, j ) )
#                 self.addLink( host, switch, **_opts)
#             # Connect switch to previous
#             if lastSwitch:
#                 self.addLink( switch, lastSwitch, **_opts )
#             lastSwitch = switch


def resourceTest(pmToTest, nSw, expLen, bw, pktSize):

    traceFilesRemote = {}
    traceFilesLocal = {}
    pms = {'cap31':0, 'cap32':1, 'cap33':2}

    ### Create linear topology ###
    lt = LinearTopo(nSw, 1, 500, 0.1)
    # lt = MyLinearTopo(nSw, 1, bw=500, delay='100ms')
    hosts = lt.hosts()
    client, server = hosts[nSw-1], hosts[0]
    switches = lt.switches()
    clientSw, serverSw = switches[nSw-1], switches[0]

    ### Create mapping between host and switches and workers ###
    mapping = {x:pms[pmToTest] for x in hosts+switches}
    pmsToHelp = pms.keys()
    pmsToHelp.remove(pmToTest)
    mapping[client] = mapping[clientSw] = pms[pmsToHelp[1]]
    mapping[server] = mapping[serverSw] = pms[pmsToHelp[0]]

    # Create cluster
    cluster = maxinet.Cluster(minWorkers=3, maxWorkers=3)

    # for thrput in [100, 300, 500]: # range(100, 501, 50):
        # rate = 10000*(nSw-3)/thrput
        # bw = thrput/(nSw-3)
        # for r in range(repeat):
            # nPkts = 1000000*expLen/rate
    # outputFile.write('+++++ bw %d, rate %d,  run %d +++++\n' % (thrput, rate, r))

    exp = maxinet.Experiment(cluster, lt, nodemapping=mapping)
    exp.setup()
    # exp.monitor()

    path = [server] + lt.switches(sort=True) + [client]
    logger.info('Server to client: %s', ' => '.join(path))
    addPathFlowRules(lt, exp, path)

    # print exp.get_node('h1').cmd('ifconfig')  # call mininet cmd function of h1

    # print 'waiting 10 seconds for routing algorithms on the controller to converge'
    # sleep(10)

    serverIP = exp.get_node(server).IP()
    print exp.get_node(client).cmd('ping -c 3 %s' % (serverIP))

    # exp.CLI(locals(), globals())

    ### Start bwm-ng ###
    for worker in exp.cluster.workers():
        wName = worker.hn()
        swIntfs = worker.run_cmd("ip link list | grep s[0123456789]*-eth | awk -F '[ @]' '{print $2}'").split()
        # bwmTraces = '/tmp/bwm-out-%s.log' % (wName)
        # # bwmCmd = 'rm bwm-out-%s.log;sleep %d;bwm-ng -t 1000 -o csv -T rate -F bwm-out-%s.log -I %s' % (wName, warmup, wName, ','.join(swIntfs))
        # bwmCmd = 'rm %s;bwm-ng -t 1000 -o csv -T rate -F %s -I %s' % \
        #     (bwmTraces, bwmTraces, ','.join(swIntfs+['em1']))
        # worker.daemonize(bwmCmd)

        netTraceFile = '/tmp/net-out-%s.{nic}.csv' % (wName)
        resmonTraceFile = '/tmp/resmon-out-%s.csv' % (wName)
        # cpuTrace = '/tmp/maxinet_cpu_%d_(%s).log' % (exp.hostname_to_workerid[wName], wName)
        traceFilesRemote[wName] = [resmonTraceFile] + [netTraceFile.replace('{nic}', x) for x in swIntfs] # First file is resource trace, rest are NIC traces

        logger.info('Monitoring veths on %s: %s', wName, ','.join(swIntfs+['em1']))
        resmonCmd = '/home/cao/python-resmon/resmon/resmon.py --outfile %s --nic %s --nic-outfile %s --flush' % \
            (resmonTraceFile, ','.join(swIntfs+['em1']), netTraceFile)
        worker.daemonize(resmonCmd)


    ### Start iperf traffic ###
    logger.info('Starting traffic')
    exp.get_node(server).cmd('iperf -s -u -i 1 > iperf-udp-server.out &')
    # exp.get_node(h).cmd('iperf -s -u -i 1 > %s &' % fileName)
    exp.get_node(client).cmd('iperf -c %s -t %d -u -b %dm -l %d -i 1' % (serverIP, expLen, bw, pktSize))
    # exp.get_node(client).cmd('sudo hping3 --udp --quiet --interval u%d --data 1250 --count %d %s' % (rate, nPkts, serverIP))

    for worker in exp.cluster.workers():
        wName = worker.hn()
        traceFilesLocal[wName] = []
        # bwmTrace = 'bwm-out-%s.log' % (wName)
        # cpuTrace = 'maxinet_cpu_%d_(%s).log' % (exp.hostname_to_workerid[wName], wName)
        # traces[wName] = [bwmTrace, cpuTrace]
        # worker.run_cmd('sudo pkill bwm-ng')
        # worker.run_cmd('sudo pkill iperf3')
        for f in traceFilesRemote[wName]:
            worker.get_file(f, './')
            traceFilesLocal[wName].append(f.split('/')[-1])
        # worker.get_file('/tmp/'+bwmTrace, './')
        # worker.get_file('/tmp/'+cpuTrace, './')

    exp.stop()
    # sleep(10)
    print '***** Test compeleted *****'

    return traceFilesLocal


def main():

    parser = argparse.ArgumentParser(description='Run a single PM resource quantification experiment')

    parser.add_argument('--nSw',
                        dest='nSw',
                        action='store',
                        help='Number of switches to create',
                        type=int,
                        default=7,
                        )

    parser.add_argument('--throughput',
                        dest='thput',
                        action='store',
                        help='Throughput to test on switch',
                        type=int,
                        default=500,
                        )

    parser.add_argument('--pktSize',
                        dest='pktSize',
                        action='store',
                        help='Packet size to use',
                        # type=int,
                        default=1250,
                        )

    parser.add_argument('--testPM',
                        dest='testPM',
                        action='store',
                        help='The PM to test',
                        default='cap32',
                        )

    parser.add_argument('--expLen',
                        dest='expLen',
                        action='store',
                        help='Duration of a single experiment',
                        # type=,
                        default=100,
                        )

    parser.add_argument('--output',
                        dest='outF',
                        action='store',
                        help='Output file',
                        default='resource_exp_output.out',
                        )

    args = parser.parse_args()
    # nSw = int(sys.argv[1])
    # thrput = int(sys.argv[2])
    # pktSize = int(sys.argv[3])
    # pmToTest =sys.argv[4]
    # fName = sys.argv[5]
    
    # expLen = 100
    bw = args.thput / (args.nSw - 3)

    traces = resourceTest(args.testPM, args.nSw, args.expLen, bw, args.pktSize)
    outputFile = open(args.outF, 'a+')
    # parseTrace(traces[args.testPM][0], traces[args.testPM][1].replace('(','\(').replace(')','\)'), outputFile)
    parseResmonTraces(traces[args.testPM][0], traces[args.testPM][1:], outputFile)
    outputFile.close()



if __name__ == '__main__':

    main()
    


    # For hping3
    # rate = 10000*(nSw-3)/thrput
    # nPkts = 1000000*expLen/rate
    # For iperf3
    # testConfigs = {
    # # 2:['1.20GHz', '1.86GHz', '2.39GHz'],
    # 4:['1.20GHz', '1.86GHz', '2.39GHz'],
    # }

    # pmToTest = 'cap32'

    # for core in testConfigs:
    #     for freq in testConfigs[core]:
    #         logger.info('+++ %d Cores @ %s on %s', core, freq, pmToTest)
    #         fName = '%dcoreAT%s-%s.data' % (core, freq, pmToTest)
    #         outputFile = open(fName, 'w', 0)
    #         for nSw in [7]:
    #             logger.info('+++ %d switches', nSw)
    #             outputFile.write('##### %d switches #####\n' % nSw)
    #             outputFile.write('tx rx pi po cpu\n')
    #             for thrput in [100, 200]:
    #                 bw = thrput/(nSw-3)
    #                 traces = resourceTest(nSw, expLen, bw)
    #                 parseTrace(traces[pmToTest][0], traces[pmToTest][1].replace('(','\(').replace(')','\)'), outputFile)
    #                 sleep(10)
    #             outputFile.write('\n')
    #         outputFile.close()

                
