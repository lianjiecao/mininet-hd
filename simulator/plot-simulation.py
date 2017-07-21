import numpy as np
import subprocess as sp
import sys, itertools, argparse, math
from scipy.stats import sem

import matplotlib, subprocess
matplotlib.use('Agg')
import pylab as plt

colorLabels = ['g', 'b', 'r', 'y' ,'c', 'm']
measures = {'MaxOver':2, 'MeanOver':3, 'NormMeanOver':4, 'MinCut':5, 'Runtime':6}
# algLabels = {'BALANCED':'Equal', 'MAX_CPU':r'$\mathregular{Max_i}$', \
#     'MAX_CPU_N':r'$\mathregular{Mul_i\times Max_i}$',\
#     'C90':r'$\mathregular{C_i(0.9)}$', 'WATERFALL':'Waterfall'}

# algLabels = {'BALANCED':'Equal', 'MAX_CPU':r'$\mathregular{U^i}$', \
#     'MAX_CPU_N':r'$\mathregular{\theta^{i} \times U^i}$',\
#     'C90':r'$\mathregular{C^i(0.9)}$', 'WATERFALL':'Waterfall'}

algLabels = {'BALANCED':r'$Equal$', 'MAX_CPU':r'$U^{\ i}$', \
    'MAX_CPU_N':r'$\theta^{\ i} \times U^{\ i}$',\
    'C90':r'$C^{\ i}(0.9)$', 'WATERFALL':r'$Waterfall$'}

TopoNames = {'rocketfuel':'RocketFuel', 'fattree':'Fat-tree', 'jellyfish':'Jellyfish'}

def parseRawCSV(rawFile):

    # {(topoType, alg):[[Num_PM_Used, Num_PM_Overloaded, Max_Overload, Mean_Overload, Norm_Mean_Overload, Min_Cut, Runtime], ...], ..}
    stats = {}
    details = {}
    with open(rawFile, 'r') as rawF:
        for line in rawF:
            tmp = line.split(';')
            pmStats = tmp[0].split(',')
            pmDetails = tmp[1].split(',')
            stats.setdefault((pmStats[0].split('-')[0], pmStats[1]), []).append([float(x) for x in pmStats[2:9]])
            details.setdefault((pmStats[0].split('-')[0], pmStats[1]), []).append([float(x) for x in pmDetails])

    return stats, details


def plotStatsData(stats, underStats, m, figFile):

    statsOfMeasure = {x:[y[measures[m]] for y in stats[x]] for x in stats.keys()}
    mincut = {x:sum([y[measures['MinCut']] for y in stats[x]]) for x in stats.keys()}
    # mincutSum = {}
    print '-------------- Min Cut --------------'
    for k in mincut:
        print k, mincut[k]/mincut[(k[0], 'WATERFALL')]

    topoTypes = sorted(list(set([x[0] for x in stats.keys()])))
    algs = sorted(list(set([x[1] for x in stats.keys()])))

    ind = np.arange(len(topoTypes))  # the x locations for the groups
    width = 0.1       # the width of the bars
    colors = itertools.cycle(colorLabels[:len(algs)])

    fig, ax = plt.subplots()
    yMax = [0, 0]
    for i,alg in enumerate(algs):
        measureAvg = [np.mean(statsOfMeasure[(x,alg)]) for x in topoTypes]
        measureSte = [sem(statsOfMeasure[(x,alg)]) for x in topoTypes]
        underAvg = [underStats[(x,alg)][0] for x in topoTypes]
        underSte = [underStats[(x,alg)][1] for x in topoTypes]

        yMax = [max(underAvg)*-1 if max(underAvg)*-1 < yMax[0] else yMax[0], 
            max(measureAvg) if max(measureAvg) > yMax[1] else yMax[1]]

        print 'Over-utils', alg, measureAvg, measureSte
        print 'Under-utils', alg, underAvg, underSte
        c = colors.next()
        ### Plot over-utils bars ###
        ax.bar(ind + .2 + width*i, measureAvg, width, color=c, label=algLabels[alg], yerr=[x/2 for x in measureSte], \
            error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1))
        ### Plot under-utils bars ###
        ax.bar(ind + .2 + width*i, [-x for x in underAvg], width, color=c, yerr=[-x/2 for x in underSte], \
            error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1), hatch = 3*'/')

    ax.set_xticks(ind + 0.1 + (len(topoTypes))*width)
    ax.set_xticklabels([TopoNames[x] for x in topoTypes])
    plt.xticks(fontsize=16)

    # print yMax
    # ylims = [np.ceil(x*1.3*10)/10 for x in yMax]
    ylims = [-0.8, 0.5] # [-0.5, 1.1] [-0.8, 0.5]
    plt.ylim(ylims[0], ylims[1])
    plt.yticks(np.arange(ylims[0], ylims[1], 0.1), fontsize=16)

    fig.canvas.draw()
    # ax.yaxis.set_label_coords(-0.08, 0.42)
    ax.yaxis.set_label_coords(-0.08, 0.53)
    ax.set_ylabel('Under-utilization           Over-utilization', fontsize=16)
    ylabels = [item.get_text() for item in ax.get_yticklabels()]
    for i in range(len(ylabels)):
        if u'\u2212' in ylabels[i]:
            ylabels[i] = ylabels[i][1:]
    # print ylabels
    ax.set_yticklabels(ylabels)
    plt.yticks(fontsize=16)

    ax.legend(loc='upper center', ncol=3, fontsize=16, labelspacing=0.5, columnspacing=0.5)
    plt.grid()
    plt.savefig('%s.png' % (figFile), bbox_inches='tight')
    #plt.savefig('%s.eps' % (figFile), format='eps', bbox_inches='tight', dpi=300)

    return


def calcUnderUtils(details):
    print '-------------- Under Utilization --------------'
    underDetails = {}
    underStats = {}

    for key in details:
        for item in details[key]:
            tmp = [1-x for x in item if x > 0 and x < 1]
            if len(tmp) > 1:
                tmp.remove(max(tmp))
                underDetails.setdefault(key, []).append(tmp)
                # if key[1] == 'WATERFALL':
                # print key, tmp

    underAvg = {x:[np.mean(y) for y in underDetails[x]] for x in underDetails.keys()}
    # print underAvg

    for key in underAvg:
        print key
        print np.mean(underAvg[key]), sem(underAvg[key]) #[('fattree', 'WATERFALL')]
        underStats[key] = [np.mean(underAvg[key]), sem(underAvg[key])]
        # print underAvg[key]
        # for values in underAvg[key]:
        #     print dunderAvg[key]
        # print underAvg[key]

    return underStats


def plotStdErr(details, figFile):
    print '-------------- Standard Deviation of Utils --------------'
    stdDetails = {}
    for key in details:
        for item in details[key]:
            if min(item) != 0 and len(item) > 2:
                item.remove(min(item))
                stdDetails.setdefault(key, []).append(sem(item)) # [max(item), min(item), sem(item)]
        if key in stdDetails:
            print key, max(stdDetails[key]), np.mean(stdDetails[key]), np.median(stdDetails[key]) #, stdDetails[key]

    topoTypes = sorted(list(set([x[0] for x in stdDetails.keys()])))
    algs = sorted(list(set([x[1] for x in stdDetails.keys()])))

    ind = np.arange(len(topoTypes))  # the x locations for the groups
    width = 0.1       # the width of the bars
    colors = itertools.cycle(colorLabels[:len(algs)])

    fig, ax = plt.subplots()
    yMax = 0
    for i,alg in enumerate(algs):
        measureAvg = [np.mean(stdDetails[(x,alg)]) for x in topoTypes]
        measureSte = [sem(stdDetails[(x,alg)]) for x in topoTypes]

        print 'Std Err', alg, measureAvg, measureSte
        c = colors.next()
        ### Plot std err bars ###
        ax.bar(ind + .2 + width*i, measureAvg, width, color=c, label=algLabels[alg], yerr=[x/2 for x in measureSte], \
            error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1))


    ax.set_xticks(ind + 0.1 + (len(topoTypes))*width)
    ax.set_xticklabels([TopoNames[x] for x in topoTypes])
    plt.xticks(fontsize=16)

    # print yMax
    # ylims = [np.ceil(x*1.3*10)/10 for x in yMax]
    ylims = [0, 0.9]
    plt.ylim(ylims[0], ylims[1])
    plt.yticks(np.arange(ylims[0], ylims[1], 0.1), fontsize=16)

    # fig.canvas.draw()
    # ax.yaxis.set_label_coords(-0.08, 0.42)
    ax.set_ylabel('Standard Error', fontsize=16)
    # ylabels = [item.get_text() for item in ax.get_yticklabels()]
    # for i in range(len(ylabels)):
    #     if u'\u2212' in ylabels[i]:
    #         ylabels[i] = ylabels[i][1:]
    # # print ylabels
    # ax.set_yticklabels(ylabels)
    # plt.yticks(fontsize=16)

    ax.legend(loc='upper center', ncol=3, fontsize=16, labelspacing=0.5, columnspacing=0.5)
    plt.grid()
    # plt.savefig('%s.png' % (figFile), bbox_inches='tight')
    plt.savefig('%s.eps' % (figFile), format='eps', bbox_inches='tight', dpi=300)



def main():
    parser = argparse.ArgumentParser(description="Plot simulation results")

    # parser.add_argument('--data-file', '-d',
    #                     dest="dataFile",
    #                     action="store",
    #                     help="Data file of simulation results",
    #                     type=str,
    #                     # default='METIS',
    #                     # required=True,
    #                     )

    parser.add_argument('--raw-file', '-r',
                        dest="rawFile",
                        action="store",
                        help="Raw file of simulation results",
                        type=str,
                        # default='METIS',
                        required=True,
                        )

    parser.add_argument('--measure', '-m',
                        dest="m",
                        action="store",
                        help="Measure to plot: MaxOver, MeanOver, NormMeanOver, MinCut, Runtime",
                        type=str,
                        default='MaxOver',
                        # required=True,
                        )

    args = parser.parse_args()

    if args.rawFile:
        stats, details = parseRawCSV(args.rawFile)
        underStats = calcUnderUtils(details)
        # for key in stats.keys():
        #     print key
        #     for values in stats[key]:
        #         print values
        plotStatsData(stats, underStats, args.m, args.rawFile.split('.')[0])
        # plotStdErr(details, args.rawFile.split('.')[0])
        



if __name__ == '__main__':

    main()
