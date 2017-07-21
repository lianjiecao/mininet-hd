#! /usr/bin/python2.7

import time, operator, subprocess, math, sys, json, argparse
import numpy as np
from partitioner import Partitioner
from topoSet import TopoSet

sys.path.append('/home/cao/cs590-map/testbed_mapping_v4_2_1/')
import models

# # 2core@1.20GHz
# 1 190   0       180     -2.94350357e+00 1.99603012e+00  1.98850672e-04
# # 2core@2.39GHz
# 2 190   0       180     -2.78967675e+01 2.94608353e+00  4.47774860e-03
# # 4core@1.20GHz
# 1 390   0       360     4.18825484e+01  1.16508146e+00  3.72826105e-03
# # 4core@2.39GHz
# 2 390   0       360     9.49318331e+0   3.29031776e+00  2.88026139e-03

### All PM models ###
PMModels = [
    [1, 190, 0, 160, [-2.94350357, 1.99603012, 0.000198850672]],
    [1, 390, 0, 320, [41.8825484, 1.16508146, 0.00372826105]],
    [2, 190, 0, 160, [-27.8967675, 2.94608353, 0.00447774860]],
    [2, 390, 0, 320, [9.49318331, 3.29031776, 0.00288026139]],
]


def genTopos(topoType='all', topoSizes = range(50, 701, 20)):
    '''
    Generate topologies based on topology type and size 
    and dump them to .graph and .host files
    '''

    topos = set()
    rfSizes = [11, 172, 201, 240, 318, 604, 624, 631, 960]
    # topoSizes = range(50, 701, 20)
#    topoSizes = range(50, 81, 20)

    # topoType = 'all' # 'jellyfish', 'fattree', 'rocketfuel' , 'clos'
    for i in topoSizes: # rfSizes is the number of switches
        t = TopoSet(i, typeTopo=topoType, bw=10) # 'threetier' 'all' 'rocketfuel'
        t.genTopo()
        tmpTopo = t.getTopoWKey()
        # print tmpTopo
        for t in tmpTopo:
            topoName = '%s-%dsw' % (t, len(tmpTopo[t][0].switches()) )
            topos.add(topoName)
            parti = Partitioner(tmpTopo[t][0])
            parti.dumpGraph(topoName)
            # print topoName

    return list(topos)


def getTopoWeight(topos):
    '''
    Read topology files and compute the weights
    '''

    topoWeights = []
    for topo in topos:
        gfName = '%s.graph' % topo
        hfName = '%s.host' % topo
        # tw, h = 0, 0
        hostCPU = []
        nodeWeights = []
        with open(gfName, 'r') as gF:
            gF.readline()
            for line in gF:
                nw = nodeWeights.append(float(line.strip().split()[1]))
        with open(hfName, 'r') as hF:
            for line in hF:
                hostCPU.append(float(line.strip()))
        topoInfo = (topo, sum(nodeWeights), max(nodeWeights), sum(hostCPU))
        print ' '.join(map(str, topoInfo))
        topoWeights.append(topoInfo)
        # print topo, w, h

    return topoWeights


def genPMFile(topoWeights, cluster_size):
    '''
    Generate PM cluster files
    '''

    minNodeOnPM = 5
    extraRes = 1 # 0.7 # 1. # 0.6

    ### Calculate weight of switches and convert vhost CPU to capacity value ###
    coefs = [list(reversed(x[-1])) for x in PMModels]
    pmCapFs = [np.poly1d(x) for x in coefs]
    pmCaps = [x(y[3]) for x,y in zip(pmCapFs, PMModels)]
    vh2caps = [x(max([y[3] for y in topoWeights])) for x in pmCapFs]
    pmFNames = []
    pms2use = []

    if cluster_size == 'large':
        ### Generate one large cluster for all topologies based on max node weight and max total weight ###
        nodeWeightMax = max([x[2] for x in topoWeights])
        totalWeightMax = max([x[1] for x in topoWeights]) + np.median(vh2caps)
        scaler = math.ceil(minNodeOnPM * nodeWeightMax / min(pmCaps))
        pms2use.append(genPMs(totalWeightMax, extraRes, pmCaps, scaler))
        pmFNames.append('%s-pm.pm' % len(pms2use[0]))
        print 'Scale factor:', scaler
    else:
        pms2use = []
        for tw in topoWeights:
            # nodeWeightMax = max([x[2] for x in topoWeights])
#            totalWeightMax = tw[1] + np.min(vh2caps)
            totalWeightMax = tw[1]
            scaler = math.ceil(minNodeOnPM * tw[2] / min(pmCaps))
            print tw[0]
            pms2use.append(genPMs(totalWeightMax, extraRes, pmCaps, scaler))
            pmFNames.append('%s.pm' % tw[0])

    for i, fName in enumerate(pmFNames):
        with open(fName, 'w') as pmF:
            pmF.write('\n'.join([ '%s %s' % (' '.join(map(str, PMModels[x[0]][:4])), \
                ' '.join(map(str, [x[1]* y for y in PMModels[x[0]][4]]))) for x in pms2use[i] ]))
        # pmFiles.append((tw[0], pmFName))

    return pmFNames, pms2use


def genPMs(topoWeight, ratio, pmCaps, scaler):
    '''
    Generate PM models
    '''

    pms = []
    i = 0
    while True:
        if not pms or topoWeight * ratio > sum([pmCaps[x[0]]*x[1] for x in pms]):
            pmIdx = i % len(PMModels)
            pms.append((pmIdx, scaler))
            i += 1
        else:
            print topoWeight, '=>', sum([pmCaps[x[0]]*x[1] for x in pms])
            break

    return pms


def calcStats(values):
    '''
    Calculate statistics of a partitioning result
    '''

    numPM = len(values) - values.count(0)
    overValues = [x-1 for x in values if x > 1]
    maxValue = np.max(overValues) if overValues else 0
    meanValue = np.mean(overValues) if overValues else 0
    normMeanValue = sum(overValues) / numPM if overValues else 0

    return [numPM, len(overValues), maxValue, meanValue, normMeanValue]


def runSimulation(topos, pmFiles, pms_idxes, cluster_size):

    # pms = [ PMModels[x[0]][:4] + [[y*x[1] for y in PMModels[x[0]][4]]] for x in pms_idx ]
    # pmCapFs = [np.poly1d(list(reversed(x[-1]))) for x in pms]
    topoTypes = list(set([x.split('-')[0] for x in topos]))
    topoSizes = sorted( [int(x.strip('sw')) for x in list(set([x.split('-')[1] for x in topos]))] )
    outputName = '%s_%ssw_%dcluster_%s.csv' % ('-'.join(topoTypes), '-'.join(map(str, [topoSizes[0], topoSizes[-1]])), \
        len(pmFiles), cluster_size)
    rawOutputName = '%s_%ssw_%dcluster_%s.txt' % ('-'.join(topoTypes), '-'.join(map(str, [topoSizes[0], topoSizes[-1]])), \
        len(pmFiles), cluster_size)
    rawOutputF = open(rawOutputName, 'w')
    outF = open(outputName, 'w')
    print 'PMs selected:', [len(x) for x in pms_idxes]
    print 'Topology types:', topoTypes
    print 'Topology sizes:', topoSizes

    resMatrix = {}
    for i, topo in enumerate(topos):
        pms_idx = pms_idxes[i] if len(pmFiles) > 1 else pms_idxes[0]
        pms = [ PMModels[x[0]][:4] + [[y*x[1] for y in PMModels[x[0]][4]]] for x in pms_idx ]
        print '\n', topo 
        resMatrix[topo] = {}

        ### Run waterfall algorithm ###
        ### Create a directory to store output ###
        wf_dir = '%s-%s_cluster-wf' % (topo, cluster_size)
        subprocess.check_output('mkdir %s' % wf_dir, shell=True)
        cmd = "~/cs590-map/testbed_mapping_v4_2_1/main.py -g %s.graph -c %s.host -p %s --find-iv -o %s" \
            % (topo, topo, pmFiles[i] if len(pmFiles) > 1 else pmFiles[0], wf_dir)
            #  | grep -A 4 'Results from best to worst:' | tail -1
        print cmd 
        start = time.time()
        ret = subprocess.check_output(cmd, shell=True)
        end = time.time()
        runTime = end - start
        rawOutputF.write(ret + '\n')

        with open('%s/best_assignment_0.json' % wf_dir) as resFile:
            res = json.load(resFile)

        resMatrix[topo]['WATERFALL'] = [ float(res['result']['total_cpu_usages'][str(j)]) / (pms[j][0]*pms[j][1]) \
            if j in res['result']['pms_used'] else 0 for j in range(len(pms)) ]
        stats = calcStats(resMatrix[topo]['WATERFALL'])
        print 'WATERFALL,%s,%d,%.3f;%s' % (','.join(map(lambda x: '%.3f' % x, stats)), res['result']['min_cut'], runTime, \
            ','.join(map(lambda x: '%.3f' % x, resMatrix[topo]['WATERFALL'])))

        outF.write( '%s,%s,%s,%d,%f;%s\n' % (topo, 'WATERFALL', ','.join(map(str, stats)), res['result']['min_cut'], runTime, \
            ','.join(map(str, resMatrix[topo]['WATERFALL']))) )


        ### Run baseline algorithms ###
        bl_dir = '%s-%s_cluster-bl' % (topo, cluster_size)
        subprocess.check_output('mkdir %s' % bl_dir, shell=True)
        cmd = "~/cs590-map/testbed_mapping_v4_2_1/gen_baseline.py -g %s.graph -c %s.host -p %s -o %s" \
            % (topo, topo, pmFiles[i] if len(pmFiles) > 1 else pmFiles[0], bl_dir)
        start = time.time()
        ret = subprocess.check_output(cmd, shell=True)
        end = time.time()
        runTime = end - start
        rawOutputF.write(ret + '\n')

        with open('%s/result.json' % bl_dir) as resFile:
            res = json.load(resFile)

        for alg in res.keys():
            resMatrix[topo][alg] = [ float(res[alg]['result']['total_cpu_usages'][str(j)]) / pms[j][1] \
                if j in res[alg]['result']['pms_used'] else 0 for j in range(len(pms)) ]
            stats = calcStats(resMatrix[topo][alg])
            print '%s,%s,%d,%.3f;%s' % (alg, ','.join(map(lambda x: '%.3f' % x, stats)), res[alg]['result']['min_cut'], runTime,\
                ','.join(map(lambda x: '%.3f' % x, resMatrix[topo][alg])))

            outF.write( '%s,%s,%s,%d,%f;%s\n' % (topo, alg, ','.join(map(str, stats)), res[alg]['result']['min_cut'], runTime, \
                ','.join(map(str, resMatrix[topo][alg]))) )


        ### Remove all results files ###
        cmd = 'rm -r %s %s' % (wf_dir, bl_dir)
        subprocess.call(cmd, shell=True)

    rawOutputF.close()
    outF.close()


def removeTopoFiles(topos, pmFiles):

    for t in topos:
        cmd = 'rm %s.graph %s.host' % (t, t)
        subprocess.call(cmd, shell=True)

    cmd = 'rm %s' % ' '.join(pmFiles)
    subprocess.call(cmd, shell=True)
    return


def checkClusterArg(clt):
    '''
    Check if cluster size is small, medium or large
    '''

    clt_avl_sizes = {'s':'small', 'm':'medium', 'l':'large'}
    clt = clt.lower()
    # clt_size = 'large'
    if clt[0] not in clt_avl_sizes:
        print 'Warning: Unknow cluster size, reset to large!'
        return 'large'

    return clt_avl_sizes[clt[0]]


def main():
    parser = argparse.ArgumentParser(description="Partitioning simulation")

    parser.add_argument('--cluster-size',
                        dest='clt',
                        action='store',
                        help='Size of clusters: small, medium, large',
                        type=str,
                        default='large',
                        )

    parser.add_argument('--topo-type',
                        dest='topo_type',
                        action='store',
                        help='Topology types',
                        type=str,
                        default='all',
                        )

    parser.add_argument('--topo-size-start',
                        dest='topo_size_start',
                        action='store',
                        help='Size of topoploy start',
                        type=int,
                        default=50,
                        )

    parser.add_argument('--topo-size-end',
                        dest='topo_size_end',
                        action='store',
                        help='Size of topoploy end',
                        type=int,
                        default=701,
                        )

    args = parser.parse_args()

    cluster_size = checkClusterArg(args.clt)
    topos = genTopos(args.topo_type, range(args.topo_size_start, args.topo_size_end, 20))
    topoWeights = getTopoWeight(topos)
    pmFiles, pms = genPMFile(topoWeights, cluster_size)
    
    runSimulation(topos, pmFiles, pms, cluster_size)
    removeTopoFiles(topos, pmFiles)



if __name__ == '__main__':
    main()



# {
#     "rank": {
#         "min_cut": 1190,
#         "pms_over": 0,
#         "pms_over_degree": 0,
#         "pms_under": 0,
#         "pms_unused": 3,
#         "pms_used": 3,
#         "tier": 0
#     },
#     "result": {
#         "assignment": "(ignored.)",
#         "min_cut": 1190,
#         "pms_over": {},
#         "pms_under": {},
#         "pms_unused": [
#             2
#         ],
#         "pms_used": [
#             1,
#             3,
#             5
#         ],
#         "share_weights": {
#             "1": 0.456349,
#             "2": 0.0,
#             "3": 1.015873,
#             "5": 0.527778
#         },
#         "switch_cap_usages": {
#             "1": 1980,
#             "2": 0,
#             "3": 3480,
#             "5": 2100
#         },
#         "switch_cpu_usages": {
#             "1": 372,
#             "2": 0,
#             "3": 784,
#             "5": 387
#         },
#         "total_cpu_usages": {
#             "1": 379,
#             "2": 0,
#             "3": 804, / 390 
#             "5": 396
#         },
#         "vhost_cpu_usages": {
#             "1": 7,
#             "2": 0,
#             "3": 20,
#             "5": 9
#         }
#     }
# }


# {
#     "BALANCED": {
#     },
#     "C90": {
#     },
#     "MAX_CPU": {
#     },
#     "MAX_CPU_N": {
#     }
# }

