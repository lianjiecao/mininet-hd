import simulatorFunc
#from metisPartitioner1 import Partitioner as metisPartitioner1
#from metisPartitioner2 import Partitioner as metisPartitioner2
#from metisPartitioner3 import Partitioner as metisPartitioner3
#from metisPartitioner4 import Partitioner as metisPartitioner4
#from chacoPartitioner  import Partitioner as chacoPartitioner
#from kahipPartitioner  import Partitioner as kahipPartitioner
#from esPartitioner     import Partitioner as esPartitioner
#from mininetPartitioner import Partitioner as mnPartitioner
from partitioner import MetisPartitioner, ChacoPartitioner, MininetPartitioner
from GPGA              import Partitioner as genPartitioner
from topoSet           import TopoSet
import time


k = 5
d = 2000
c = 50000
c1 = c/k-d*(k-1)/2
ck = c1+(k-1)*d
#capacities = sorted(range(c1, ck+1, d), reverse=True) # , 1000.0, 1000.0
capacities = [1000, 1000, 1000, 1000]
print capacities
workerShares = [capacities[x]/sum(capacities) for x in range(len(capacities))]


rfSizes = [11, 172, 201, 240, 318, 604, 624, 631, 960] #[11, 172, 201, 240, 318]#[11, 172, 201, 240, 318, 604, 624, 631, 960] # 

origTopologies = {'fattree':[], 'jellyfish':[], 'clos':[], 'rocketfuel':[]}
topoSizes = range(50, 500, 50) # [11, 172, 201, 240, 318, 604, 624, 631, 960] # range(50, 500, 50)
for i in topoSizes: # rfSizes is the number of switches
    t = TopoSet(i, typeTopo='all') # 'threetier' 'all' 'rocketfuel'
    t.genTopo()
    tmpTopo = t.getTopoWKey()
    for tType in tmpTopo:
        origTopologies[tType] += tmpTopo[tType]

partitioners = {
#    "metisNoWeight":metisPartitioner1, 
#    "metisEdgeWeight":metisPartitioner2, 
#    "metisVertWeight":metisPartitioner3, 
    'metis':MetisPartitioner,
    'chaco':ChacoPartitioner,
#    'kahip':kahipPartitioner,
#    'mn-random':mnPartitioner,
    'mn-roundRobin':MininetPartitioner,
#    'mn-switchBin':mnPartitioner,
#    'mn-hostSwitchBin':mnPartitioner,
#    "easyScale":esPartitioner,
    # "Genetic":genPartitioner
    } #"metisEdgeVertWeight":metisPartitioner4,, "Genetic":genPartitioner, , "easyScale":esPartitioner


for tType in ['rocketfuel', 'fattree', 'jellyfish', 'clos']:  # 'threetier' 'fattree', 'jellyfish', 'clos' , 'rocketfuel'
    print "\n++++++++++", tType, "topology ++++++++++"
    for topo in origTopologies[tType]:
        # topo = origTopologies[t]
        print ""

        tWeight = simulatorFunc.checkTopoSimple(topo)
        newCap = simulatorFunc.adjustCap(tWeight, capacities)
#        theoSol = simulatorFunc.calcTheoSol(tWeight, newCap)
        theoSol = [100, 100, 100, 100]
        # print "Theoretical solution:", theoSol
        metisShare = [float(theoSol[i])/float(sum(theoSol)) for i in range(len(theoSol)) if theoSol[i] != 0]
        geneCoeff = [1.0 for x in range(len(capacities))]
        if tWeight > 0.9*sum(newCap):
            geneCoeff = [1.05 for x in range(len(capacities))]
        geneCap = [geneCoeff[i]*newCap[i] for i in range(len(newCap))]
    
        subTopos = {}

        for p in partitioners:
#            start = time.time()
            parti = partitioners[p](topo)
#            parti.loadtopo(topo)
            # print "Switches:", topo.switches()
            if p is 'Genetic':
                subTopo = parti.partition(len(geneCap), geneCap)
                subTopos[p] = subTopo.values()
                # simulatorFunc.evalPart(topo, capacities, subTopo)
            else:
                subTopo = parti.partition(len(metisShare), alg=p) # Equal partition
                # subTopo = parti.partition(len(metisShare), metisShare) # Partition based on share
                # simulatorFunc.evalPart(topo, capacities, subTopo.getTopos())
                subTopos[p] = subTopo.getTopos()
#                end = time.time()
#                for subT in subTopos[p]:
#                    print 'swiches:', subT.switches()
#                    print 'hosts:', subT.hosts()
                #print '=====', p, int(end-start), 'sec'
        simulatorFunc.printRes(topo, capacities, theoSol, subTopos)


# topo = origTopologies["jellyfish"]
# simulatorFunc.checkTopo(topo)
# genParti = genPartitioner()
# genParti.loadtopo(topo)
# subTopo = genParti.partition(len(capacities), capacities)

# print subTopo
# # for l in topo.links():
# #     print topo.linkInfo(l[0], l[1])
# for l in subTopo[0].links():
#     print l
#     print subTopo[0].linkInfo(l[0], l[1])
# print subTopo[0].switches()

# simulatorFunc.evalPart(topo, workerShares, subTopo)


