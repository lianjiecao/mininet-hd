import numpy as np
import subprocess as sp
import sys, itertools, argparse

import matplotlib, subprocess
matplotlib.use('Agg')
import pylab as plt

pms = {'PM1':'cap34', 'PM2':'cap31', 'PM3':'cap32', 'PM4':'cap35', 'PM5':'cap33', 'PM6':'cap36'}
# mapAlgs = ['MN-SBP', 'D-METIS', 'US-METIS', 'UC-MKL']
# mapAlgs = ['SwitchBinPlacer', 'Equal-METIS', 'Share-METIS' ,'Waterfall']
colorLabels = ['g', 'b', 'r', 'y' ,'c', 'm']
# colors = itertools.cycle(('g', 'b', 'r', 'y' ,'c', 'm')) # 'c', 
# algLabels = {'Equal-METIS':'Equal', 'MAX_CPU':r'$\mathregular{Max_i}$', \
#     'MAX_CPU_N':r'$\mathregular{Mul_i\times Max_i}$', 'SwitchBinPlacer':'SwitchBin', \
#     'C90':r'$\mathregular{C_i(0.9)}$', 'Waterfall':'Waterfall', \
#     'C90_5PM':r'$\mathregular{C_i(0.9)}_5PM$', 'C90_6PM':r'$\mathregular{C_i(0.9)}$_6PM'}

algLabels = {'Equal-METIS':r'$Equal$', 'MAX_CPU':r'$U^{\ i}$', \
    'MAX_CPU_N':r'$\theta^{\ i} \times U^{\ i}$', 'SwitchBinPlacer':r'$SwitchBin$', \
    'C90':r'$C^{\ i}(0.9)$', 'Waterfall':r'$Waterfall$', \
    }

def plotData(fileName, size):

    picPrefix = fileName.split('.')[-2]
    ddosDataF = open(fileName, 'r').read()
    ddosData = {}

    ret = subprocess.check_output("cat %s | awk '{print $2}'" % fileName, shell=True)
    mapAlgs = list(set(ret.split()))
    colors = itertools.cycle(colorLabels[:len(mapAlgs)])

    for line in ddosDataF.strip().split('\n'):
        tokens = line.split()
        ddosData.setdefault(tokens[0], {})
        ddosData[tokens[0]][tokens[1]] = [float(x) for x in tokens[2:]]

    N = len(pms)

    ind = np.arange(N)  # the x locations for the groups
    width = 0.15       # the width of the bars

    fig1, ax = plt.subplots()

    i = 0
    for m in mapAlgs:
        c = colors.next()
        i += 1
        ax.bar(ind + width*i, ddosData['cpuRF'+size][m], width, color=c, yerr= ddosData['cpuErrRF'+size][m], label=algLabels[m], \
        error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1)) # 

    ax.set_ylabel('CPU Utilization', fontsize=18)
    ax.set_title('Normalized CPU Utilization', fontsize=18)
    ax.set_xticks(ind + (len(ddosData['cpuRF'+size])-1)*width)
    ax.set_xticklabels(sorted(pms.keys()))
    ax.legend(loc='upper center', ncol=2, fontsize=18, labelspacing=0.5, columnspacing=0.5)

    plt.ylim(0, 1.5)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid()
    plt.savefig('%s-cpu.png' % picPrefix, bbox_inches='tight')
    # plt.savefig('%s-cpu.eps' % picPrefix, format='eps', bbox_inches='tight', dpi=1000)

    fig2, ax = plt.subplots()

    i = 0
    for m in mapAlgs:
        c = colors.next()
        i += 1
        ax.bar(ind + width*i, ddosData['linkRF'+size][m], width, color=c, yerr=ddosData['linkErrRF'+size][m], label=algLabels[m], \
        error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1)) # 

    ax.set_ylabel('Link Utilization', fontsize=18)
    ax.set_title('Normalized Link Utilization', fontsize=18)
    ax.set_xticks(ind + (len(ddosData['cpuRF'+size])-1)*width)
    ax.set_xticklabels(sorted(pms.keys()), fontsize=18)
    ax.legend(loc='upper center', ncol=2, fontsize=18, labelspacing=0.5, columnspacing=0.5)

    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.ylim(0, 1.5)
    plt.grid()
    plt.savefig('%s-link.png' % picPrefix, bbox_inches='tight')
    # plt.savefig('%s-link.eps' % picPrefix, format='eps', bbox_inches='tight', dpi=1000)

    fig3, ax = plt.subplots()

    for m in mapAlgs:
        c = colors.next()
        ax.plot(range(len(ddosData['httpRF'+size][m])), ddosData['httpRF'+size][m], linestyle = '-', linewidth=3, color=c, label=algLabels[m])

    ax.set_ylabel('HTTP Throughput', fontsize=18)
    ax.set_xlabel('Time (second)', fontsize=18)
    ax.set_title('Normalized HTTP Throughput', fontsize=18)
    ax.legend(loc='upper right', ncol=2, fontsize=18, labelspacing=0.5, columnspacing=0.5)
    plt.ylim(0, 1.5)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid()
    plt.savefig('%s-http.png' % picPrefix, bbox_inches='tight')
    # plt.savefig('%s-http.eps' % picPrefix, format='eps', bbox_inches='tight', dpi=1000)


def plotData2(fileName, size):
    colorLabels = ['g', 'b', 'r', 'y' ,'c', 'm']

    picPrefix = fileName.split('.')[-2]
    ddosDataF = open(fileName, 'r').read()
    ddosData = {}

    mapAlgs = []
    for line in ddosDataF.strip().split('\n'):
        if line.strip().startswith('#') or line == '':
            continue
        tokens = line.split(',')
        # print tokens
        ddosData.setdefault(tokens[0], {})
        if tokens[1] not in mapAlgs:
            mapAlgs.append(tokens[1])
        ddosData[tokens[0]][tokens[1]] = [float(x) for x in tokens[2:]]


    # for m in mapAlgs:
    numPMs = len(pms)
    xlabels = sorted(pms.keys())
    ind = np.arange(len(mapAlgs)) # the x locations for the groups
    width = 0.13       # the width of the bars
    colors = itertools.cycle(colorLabels[:numPMs])

    print mapAlgs
    fig1, ax = plt.subplots()
    for i in range(numPMs):
        # i += 1
        data = [ddosData['cpuRF'+size][x][i] for x in mapAlgs]
        dataErr = [ddosData['cpuErrRF'+size][x][i] for x in mapAlgs]
        c = colors.next()
        ax.bar(ind + width*i, data, width, color=c, label=xlabels[i], yerr= [x/2 for x in dataErr], \
            error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1)) # 

    ax.set_ylabel('CPU Utilization', fontsize=18)
    # ax.set_title('Normalized CPU Utilization', fontsize=18)
    ax.set_xticks(ind + (len(mapAlgs)-3)*width)
    # ax.set_xticklabels(xlabels, rotation=40, ha=ha[n])
    ax.set_xticklabels([algLabels[x] for x in mapAlgs], rotation=15, ha='center')
    ax.legend(loc='upper center', ncol=3, fontsize=18, labelspacing=0.5, columnspacing=0.5)

    plt.ylim(0, 1.4)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid()
    # plt.savefig('%s-cpu.png' % picPrefix, bbox_inches='tight')
    plt.savefig('%s-cpu.eps' % picPrefix, format='eps', bbox_inches='tight', dpi=300)

    fig2, ax = plt.subplots()
    for i in range(numPMs):
        # i += 1
        data = [ddosData['linkRF'+size][x][i] for x in mapAlgs]
        dataErr = [ddosData['linkErrRF'+size][x][i] for x in mapAlgs]
        c = colors.next()
        ax.bar(ind + width*i, data, width, color=c, label=xlabels[i], yerr= [x/2 for x in dataErr], \
            error_kw=dict(ecolor='black', lw=1, capsize=4, capthick=1)) # 

    ax.set_ylabel('Link Utilization', fontsize=18)
    # ax.set_title('Normalized Link Utilization', fontsize=18)
    # ax.set_xticks(ind + (len(mapAlgs)-1)*width)
    ax.set_xticks(ind + (len(mapAlgs)-3)*width)
    ax.set_xticklabels([algLabels[x] for x in mapAlgs], rotation=15, ha='center')
    # ax.set_xticklabels(mapAlgs)
    ax.legend(loc='upper center', ncol=3, fontsize=18, labelspacing=0.5, columnspacing=0.5)

    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.ylim(0, 1.4)
    plt.grid()
    # plt.savefig('%s-link.png' % picPrefix, bbox_inches='tight')
    plt.savefig('%s-link.eps' % picPrefix, format='eps', bbox_inches='tight', dpi=300)

    fig3, ax = plt.subplots()

    for m in mapAlgs:
        c = colors.next()
        ax.plot(range(len(ddosData['httpRF'+size][m])), ddosData['httpRF'+size][m], linestyle = '-', \
            linewidth=3, color=c, label=algLabels[m])

    ax.set_ylabel('HTTP Throughput', fontsize=18)
    ax.set_xlabel('Time (second)', fontsize=18)
    # ax.set_title('Normalized HTTP Throughput', fontsize=18)
    ax.legend(loc='upper center', ncol=3, fontsize=18, labelspacing=0.2, columnspacing=0.3)

    plt.ylim(0, 1.5)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid()
    # plt.savefig('%s-http.png' % picPrefix, bbox_inches='tight')
    plt.savefig('%s-http.eps' % picPrefix, format='eps', bbox_inches='tight', dpi=300)


def main():
    parser = argparse.ArgumentParser(description="Plot DDoS experiment results")

    parser.add_argument('--data-file',
                        dest="fileName",
                        action="store",
                        help="Data file of DDoS experiments",
                        type=str,
                        # default='METIS',
                        required=True,
                        )

    parser.add_argument('--ddos-size',
                        dest="size",
                        action="store",
                        help="Size of DDoS experiment",
                        type=str,
                        required=True
                        )

    args = parser.parse_args()

    plotData2(args.fileName, args.size)


if __name__ == '__main__':
    main()