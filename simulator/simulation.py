import simulatorFunc
#from metisPartitioner1 import Partitioner as metisPartitioner1
#from metisPartitioner2 import Partitioner as metisPartitioner2
#from metisPartitioner3 import Partitioner as metisPartitioner3
#from metisPartitioner4 import Partitioner as metisPartitioner4
#from chacoPartitioner  import Partitioner as chacoPartitioner
#from kahipPartitioner  import Partitioner as kahipPartitioner
#from esPartitioner     import Partitioner as esPartitioner
#from mininetPartitioner import Partitioner as mnPartitioner
from partitioner import MetisPartitioner, ChacoPartitioner, ChacoUEPartitioner, MininetPartitioner
from GPGA              import Partitioner as genPartitioner
from topoSet           import TopoSet
import time, operator


k = 5
d = 2000
c = 50000
c1 = c/k-d*(k-1)/2
ck = c1+(k-1)*d
#newCaps = sorted(range(c1, ck+1, d), reverse=True) # , 1000.0, 1000.0
#PMs = {'cap31':1200, 'cap32':1000, 'cap33':800, 'cap34':600}
#PMs = {'cap31':12000, 'cap32':10000, 'cap33':8000, 'cap34':6000}
PMs = {'cap31':1200, 'cap32':800}
caps = sorted(PMs.items(), key=operator.itemgetter(1), reverse=True)

# workerShares = [newCaps[x]/sum(newCaps) for x in range(len(newCaps))]


rfSizes = [11, 172, 201, 240, 318, 604, 624, 631, 960] #[11, 172, 201, 240, 318]#[11, 172, 201, 240, 318, 604, 624, 631, 960] # 

origTopologies = {'fattree':[], 'jellyfish':[], 'clos':[], 'rocketfuel':[]}
topoSizes = [36] #range(50, 651, 50) # [11, 172, 201, 240, 318, 604, 624, 631, 960] # range(50, 500, 50)
for i in topoSizes: # rfSizes is the number of switches
    t = TopoSet(i, typeTopo='all') # 'threetier' 'all' 'rocketfuel'
    t.genTopo()
    tmpTopo = t.getTopoWKey()
    for tType in tmpTopo:
        origTopologies[tType] += tmpTopo[tType]

partitioners = {
#    "metisNoWeight":metisPartitioner1, 
#    "metisEdgeWeight":metisPartitioner2, 
#    "metisVertopoW":metisPartitioner3, 
    'metis':MetisPartitioner,
#    'chaco':ChacoPartitioner,
    'chacoUE':ChacoUEPartitioner,
#    'kahip':kahipPartitioner,
#    'mn-random':mnPartitioner,
#    'mn-roundRobin':MininetPartitioner,
#    'mn-switchBin':mnPartitioner,
#    'mn-hostSwitchBin':mnPartitioner,
#    "easyScale":esPartitioner,
    # "Genetic":genPartitioner
    } #"metisEdgeVertopoW":metisPartitioner4,, "Genetic":genPartitioner, , "easyScale":esPartitioner


for tType in ['rocketfuel']: #['rocketfuel', 'fattree', 'jellyfish', 'clos']:  # 'threetier' 'fattree', 'jellyfish', 'clos' , 'rocketfuel'
    print "\n++++++++++", tType, "topology ++++++++++"
    for topo in origTopologies[tType]:
        # topo = origTopologies[t]
        print ""
#        bw = 150
#        topo.addHost('h1', ip='10.0.0.1', cpu=0.05)
#        topo.addLink('h1', 's1', bw=bw, delay='1ms')
#        topo.addHost('h2', ip='10.0.0.2', cpu=0.05)
#        topo.addLink('h2', 's2', bw=bw, delay='1ms')
#        topo.addHost('h3', ip='10.0.0.3', cpu=0.05)
#        topo.addLink('h3', 's3', bw=bw, delay='1ms')
#        topo.addHost('h5', ip='10.0.0.5', cpu=0.05)
#        topo.addLink('h5', 's5', bw=bw, delay='1ms')
#        topo.addHost('h7', ip='10.0.0.7', cpu=0.05)
#        topo.addLink('h7', 's7', bw=bw, delay='1ms')
#        topo.addHost('h8', ip='10.0.0.8', cpu=0.05)
#        topo.addLink('h8', 's8', bw=bw, delay='1ms')


#        topoW = simulatorFunc.checkTopoSimple(topo)
        topoW = simulatorFunc.checkTopo(topo)
        newCaps = simulatorFunc.adjustCap(topoW, caps)
        selectedPMs = simulatorFunc.selectPMs(topoW, newCaps)
#        theoSol = simulatorFunc.calcTheoSol(topoW, newCaps)
        # theoSol = [100, 100, 100, 100]
        # print "Theoretical solution:", theoSol
        # metisShare = [float(theoSol[i])/float(sum(theoSol)) for i in range(len(theoSol)) if theoSol[i] != 0]
        # geneCoeff = [1.0 for x in range(len(newCaps))]
        # if topoW > 0.9*sum(newCaps):
        #     geneCoeff = [1.05 for x in range(len(newCaps))]
        # geneCap = [geneCoeff[i]*newCaps[i] for i in range(len(newCaps))]
    
        subTopos = {}
        for p in partitioners:
#            start = time.time()
            parti = partitioners[p](topo)
#            parti.loadtopo(topo)
            # print "Switches:", topo.switches()
            # if p is 'metis':
            #     subTopo = parti.partition(len(geneCap), geneCap)
            #     subTopos[p] = subTopo.values()
            # else:
            subTopo = parti.partition(len(selectedPMs), alg=p, shares=[x[1] for x in selectedPMs])
                # subTopo = parti.partition(len(metisShare), metisShare) # Partition based on share

            subTopos[p] = subTopo.getTopos()
            print p, '\n', len(subTopos[p][0].nodes()), subTopos[p][0].nodes(), '\n', len(subTopos[p][1].nodes()), subTopos[p][1].nodes()
#                end = time.time()
#                for subT in subTopos[p]:
#                    print 'swiches:', subT.switches()
#                    print 'hosts:', subT.hosts()
                #print '=====', p, int(end-start), 'sec'
        simulatorFunc.printRes(topo, topoW, [x[1] for x in selectedPMs], subTopos)
#        simulatorFunc.printSimpleRes(topo, topoW, [x[1] for x in selectedPMs], subTopos)


# topo = origTopologies["jellyfish"]
# simulatorFunc.checkTopo(topo)
# genParti = genPartitioner()
# genParti.loadtopo(topo)
# subTopo = genParti.partition(len(newCaps), newCaps)

# print subTopo
# # for l in topo.links():
# #     print topo.linkInfo(l[0], l[1])
# for l in subTopo[0].links():
#     print l
#     print subTopo[0].linkInfo(l[0], l[1])
# print subTopo[0].switches()

# simulatorFunc.evalPart(topo, workerShares, subTopo)


