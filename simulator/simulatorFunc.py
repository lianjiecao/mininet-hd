import sys, itertools, logging, time, math


logging.basicConfig()

logger = logging.getLogger("simuFunc")
logger.setLevel(logging.INFO)

def adjustCap(topoW, caps):

    logger.debug("Original capacities: " + str(caps))
    sumCaps = sum([x[1] for x in caps])
    if topoW > sumCaps:
        logger.debug("Topology is too large! Experiment may lose fidelity!")
        ratio = float(topoW)/sumCaps
        newCaps = [(x[0], int(ratio*x[1])) for x in caps]
        logger.debug("Adjusted capacities: " + str(newCaps))
        return newCaps
    else:
        return caps


# def initShare(origTopo, capacities):

#     tWeight = calcTopoWeight(origTopo)
#     numCap = len(capacities)
#     sumCap = float(sum(capacities))
#     shares = []
#     remWeight = tWeight

#     if tWeight <= capacities[0]:
#         shares.append(1)
#         return shares
#     else:
#         for i in range(numCap):
#             if remWeight > capacities[i]:
#                 shares.append(float(capacities[i])/tWeight)
#                 remWeight = remWeight - capacities[i]
#             elif remWeight > 0:
#                 shares.append(float(remWeight)/tWeight)
#                 remWeight = 0

#     return shares
    # shares = []

def calcMetisShare(topo, caps):
    topoW = calcTopoWeight(topo)
    subTopoW = caps[:-1]
    subTopoW.append(topoW - sum(subTopoW))
    shares = [float(x)/topoW for x in subTopoW]
    return shares

def calcTheoSol(origTopo, capacities):

    tWeight = origTopo #calcTopoWeight(origTopo)
    numCap = len(capacities)
    sumCap = float(sum(capacities))
    theoSol = [0 for x in range(len(capacities))]
    remWeight = tWeight

    if tWeight <= capacities[0]:
        theoSol[0] = tWeight
        return theoSol
    else:
        for i in range(numCap):
            if remWeight > capacities[i]:
                theoSol[i] = float(capacities[i])
                remWeight = remWeight - capacities[i]
            elif remWeight > 0:
                theoSol[i] = float(remWeight)
                remWeight = 0
    logger.info("Theoretical solution: " + str(theoSol))
    return theoSol

def selectPMs(topoW, caps):
    # TopoW: total weight of the original topology
    # caps: list of tuples ([pm, cap]) sorted by the values of the second element

    remW = topoW
    selectedPMs = []
    for item in caps:
        remW -= item[1]
        selectedPMs.append(item)
        if remW <= 0:
            break

    return selectedPMs



def objectFunc(cap, theoSol, sol):

    f1 = [0 for x in range(len(theoSol))]
    for i in range(len(sol)):
        # if theoSol[i] is not 0:
        f1[i] = pow((sol[i]-theoSol[i]), 2)
        # if sol[i] > cap[i]:
        # if sol[i] > 0:
        #     f1[i] = f1[i] + pow((sol[i]-cap[i])/cap[i], 2)

    # coeff = [(sum(theoSol)-theoSol[x])/sum(theoSol) for x in range(len(theoSol))]
    # f1 = [pow((theoSol[x]-sol[x])/theoSol[x], 2) for x in range(len(sol))]
    # f2 = [coeff[x]*pow((theoSol[x]-res[x])/theoSol[x], 2) for x in range(len(res))]
    logger.debug("f1: " + str(f1))
    # logger.debug("f2:" + str(f2))
    return pow(sum(f1),0.5)

def evalPart(origTopo, capacities, subTopos):
    """
    Evaluate the partitions of a partitioning algorithm
    origTopo: the orignial topology before partitioning
    capacities: the capacity or fraction of each PM/container
    subtopos: list of sub topologies from partitioning algorithm
    """
    # print "\t===== Evaluate Partitioning ====="
    numTopos = len(subTopos)
    numPM = len(capacities)
    if (numTopos > numPM):
        logger.error("Number of sub topologies does not match number of PMs")
        exit()
    
    weights = {x:0 for x in range(numPM)}
    cutWeights = {x:0 for x in range(numPM)}
    subLinks = list(itertools.chain(*[subTopos[x].links(sort=True) for x in range(numTopos)]))
    cuts = [x for x in origTopo.links(sort=True) if x not in subLinks]

    for i in range(numTopos):
        weights[i] = calcTopoWeight(subTopos[i])
        cutWeights[i] = 0

    # for i in range(numTopos):
    #     weights[i] = 0.0
    #     for link in subTopos[i].links():
    #         if origTopo.isSwitch(link[0]) and origTopo.isSwitch(link[1]):
    #             weights[i] = weights[i] + subTopos[i].linkInfo(link[0], link[1])["bw"]
    
    for link in cuts:
        for i in range(numTopos):
            if link[0] in subTopos[i].switches() or link[1] in subTopos[i].switches():
                weights[i] = weights[i] + origTopo.linkInfo(link[0], link[1])["bw"]
                cutWeights[i] = cutWeights[i] + origTopo.linkInfo(link[0], link[1])["bw"]

    return [weights, cutWeights]
    # return sorted(weights.values(), reverse=True)
    # wSum = sum(weights.values())
    # print "\tPart\tCap\tWeight\tFraction"
    # for x in range(numPM):
    #     print "\t%d\t%.1f\t%.1f\t%.4f" % (x, capacities[x], weights[x], weights[x]/wSum)


def calEdgeCut(origTopo, subTopos):
    return len(origTopo.links())-sum([len(x.links()) for x in subTopos])
    # for l in origTopo.links():
    #     for st in subTopos

def printRes(origTopo, topoW, cap, subTopos):

    resMatrix = []
    resMatrix.append(["Partitioner", "Capacity", "Subtopo_Weights", "Objective_Func", "EdgeCuts"])
    resMatrix.append(["-----------", "--------", "---------------", "--------------", "--------"])
    # print "\tPartitioner |\tCapacity |\tSubtopo Weights |\tFraction |"
    for p in sorted(subTopos.keys()):
        [partiSol, cutW] = evalPart(origTopo, cap, subTopos[p])
        objFunc = 0 # objectFunc(cap, theoSol, partiSol)
#        edgCut = calEdgeCut(origTopo, subTopos[p])
        # with objective function
        resMatrix.append([p, str(cap), str(sorted(partiSol.values(),reverse=True)), str(objFunc), 
            str(sorted(cutW.values(),reverse=True))])
    # col_width = max(len(item) for row in resMatrix for item in row) + 1
    col_width = []
    for i in range(len(resMatrix[0])):
        col_width.append(max([len(x[i]) for x in resMatrix]) + 3)

    print "-"*sum(col_width)
    for row in resMatrix:
        print "".join(row[x].ljust(col_width[x]) for x in range(len(row)))

    
    # print resMatrix


def printSimpleRes(origTopo, topoW, cap, subTopos):

    results = [[],[]]
    for p in sorted(subTopos.keys()):
        [partiSol, cutW] = evalPart(origTopo, cap, subTopos[p])
        subtopoW = sorted(partiSol.values(),reverse=True)
#        print p, cap, subtopoW, cutW.values()
        results[0].extend([p+'-V', p+'-E'])
        results[1].extend([sum([abs(cap[i]-subtopoW[i]) for i in range(len(cap))])/sum(cap), sum(cutW.values())/topoW])
#        print p, sum([abs(cap[i]-subtopoW[i]) for i in range(len(cap))])/sum(cap), sum(cutW.values())/topoW
    print ' '.join(results[0])
    print ' '.join(['%.6f' % x for x in results[1]])

def calcTopoWeight(topo):
    links = topo.links(sort = True)
    switches = topo.switches()
    weights = {x:0.0 for x in switches}

    for l in links:
        if topo.isSwitch(l[0]):
            weights[l[0]] = weights[l[0]] + float(topo.linkInfo(l[0], l[1])["bw"])
        if topo.isSwitch(l[1]):
            weights[l[1]] = weights[l[1]] + float(topo.linkInfo(l[0], l[1])["bw"])

    # print weights
    return sum(weights.values())

def checkTopo(topo):
    print "===== Topology info ====="
    numHost = len(topo.hosts())
    numSwitch = len(topo.switches())
    numLink = len(topo.links())
    weight = calcTopoWeight(topo)

    # for link in topo.links():
    #     if (topo.isSwitch(link[0]) and topo.isSwitch(link[1])) and topo.linkInfo(link[0], link[1]).has_key("bw"):
    #         weight = weight + topo.linkInfo(link[0], link[1])["bw"]

    print numHost, "hosts"
    print numSwitch, "switches"
    print numLink, "links"
    print weight, "total weight"

    return weight

def checkTopoSimple(topo):
#    print "===== Topology info ====="
    numHost = len(topo.hosts())
    numSwitch = len(topo.switches())
    numLink = len(topo.links())
    weight = calcTopoWeight(topo)

    # for link in topo.links():
    #     if (topo.isSwitch(link[0]) and topo.isSwitch(link[1])) and topo.linkInfo(link[0], link[1]).has_key("bw"):
    #         weight = weight + topo.linkInfo(link[0], link[1])["bw"]

#    print "switch:", numSwitch, "host:", numHost, "link:", numLink, "weight", weight

    return weight


if __name__ == "__main__":
    # print initShare(900.0, [1000.0, 600.0, 400.0])
    cap = [100.0, 60.0, 40.0]
    tw = 140
    newCap = adjustCap(tw, cap)
    theoSol = calcTheoSol(tw, newCap)
    # print "Capacities:", cap, "\n"
    sols = [[100.0, 40.0, 0.0], [100.0, 0.0, 40.0], [110.0, 30.0, 0.0], [90.0, 50.0, 0.0], [90.0, 0.0, 50.0], [100.0, 30.0, 10.0], [100.0, 10.0, 30.0]]

    for s in sols:
        print "sol:",s
        print "Value:", objectFunc(newCap, theoSol, s), "\n"


