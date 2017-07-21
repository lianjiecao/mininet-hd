import numpy as np
import subprocess as sp
import sys, itertools, argparse

import matplotlib
matplotlib.use('Agg')
import pylab as plt

colors = itertools.cycle(('g', 'b', 'r', 'y'))
marker = itertools.cycle(('*', '^', 'o', 's'))
param = {'pps': {'loc':2, 'ylim':200000}, 'mbps': {'loc':0, 'ylim':2000}}


def parseData(dataFiles, thputType):
    '''
    Parse quantification experiment raw data
    '''

    scaled_cpu_info = []
    thput_info = []
    pm_cores = []
    for dataF in dataFiles:
        cont = open(dataF,'r').read().strip()
        nCores = int(dataF[0])

        cpu = {} #[0]
        scaledCPU = {} # 100 * n_core
        thput = {} #[0]
        mod = 0.85
        nswBlks = cont.split("##### ")[1:]

        for nswBlk in nswBlks:
            lines = nswBlk.split('\n')
            nsw = lines[0].split()[0]
            cpu[nsw] = [0]
            scaledCPU[nsw] = [0]
            thput[nsw] = [0]
            for line in lines[1:]:
                tokens = line.split()
                if len(tokens) == 5 and line.replace(' ', '').isdigit():
                    if float(tokens[4]) < 90:
                        if int(nsw) == 7:
                            thput[nsw].append(float(tokens[param[thputType]['loc']])*mod)
                        else:
                            thput[nsw].append(float(tokens[param[thputType]['loc']]))
                        cpu[nsw].append(float(tokens[4]))
                        scaledCPU[nsw].append(float(tokens[4])*nCores)
        scaled_cpu_info.append(scaledCPU)
        thput_info.append(thput)
        pm_cores.append(nCores)

    return scaled_cpu_info, thput_info, pm_cores


def capFuncRegression(cpu_info, thput_info):
    '''
    Compute capacity functions using polynomial regression
    '''
    
    capfs = []
    for cpu,thput in zip(cpu_info, thput_info):
        u_cpu = np.array([x for y in cpu.values() for x in y])
        print u_cpu
        c_cap = np.array([x for y in thput.values() for x in y])
        f_cap = np.polyfit(u_cpu, c_cap, 2)
        capfs.append(np.poly1d(f_cap))

    return capfs

    # u_cpu = np.array([x for y in cpu.values() for x in y])
#    u_cpu = np.array([x for y in scaledCPU.values() for x in y])
#    c_cap = np.array([x for y in thput.values() for x in y])
#    f_cap = np.polyfit(u_cpu, c_cap, 2)

#    p = np.poly1d(f_cap)


def plotCapfs(capfs, cpu_info, thput_info, pm_cores, dataFs, thputType, fig_name):
    '''
    Plot capacity functions
    '''

    fig = plt.figure()
    for f_cap,cpu,thput,nCores,dataF in zip(capfs,cpu_info,thput_info,pm_cores,dataFs):
        p = np.poly1d(f_cap)
        # f_cap_x = range(0, 101, 10)
        f_cap_x = range(0, 100*nCores, 5*nCores)
        f_cap_y = p(f_cap_x)

        print '%s:%s (%f)' % (dataF.split('-')[0].replace('AT', '@'), f_cap, p(95*nCores))

        # print ' '.join(map(str, f_cap_x)
        # print ' '.join(map(str, f_cap_y))


        ax = fig.add_subplot(1,1,1)
        swLegends = {}
        color = colors.next()
        for nsw in sorted(cpu.keys()):
            m = marker.next()
            # ax.plot(cpu[nsw], thput[nsw], linestyle = '', marker=m, c=color, markersize=8) #, xp, p30(xp), '--') , label='%s switches' % nsw
            ax.plot(cpu[nsw], thput[nsw], linestyle = '', marker=m, c=color, markersize=8) 
            # Create custom artists
            if m == '*':
                l = plt.Line2D((0,1),(0,0), color='w', marker=m, linestyle='', markersize=10)
            else:
                l = plt.Line2D((0,1),(0,0), color='w', marker=m, linestyle='', markersize=8)
            if nsw not in swLegends:
                swLegends[int(nsw)] = [l, '%d-switch' % (int(nsw)-2)]

        label = '%s-%s' % (dataF.split('-')[0].replace('AT', '@'), dataF.split('-')[1])
        label = dataF.split('-')[0].replace('AT', '@')
        ax.plot(f_cap_x, f_cap_y, linestyle = '-', c=color, linewidth=3, label=label)


        plt.xlabel('CPU Usage (%)', fontsize=18)
        plt.ylabel('Total Throughput (%s)' % thputType, fontsize=18)
        # plt.ylim(0, 2000)
        plt.ylim(0, param[thputType]['ylim'])

    plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    #Get artists and labels for legend and chose which ones to display
    handles, labels = ax.get_legend_handles_labels()
    display = range(len(dataFs)) # (0,1,2)

    # ax.legend(loc='upper left', fontsize=12)
    #Create legend from custom artist/label lists
    ax.legend([handle for i,handle in enumerate(handles) if i in display]+[swLegends[x][0] for x in sorted(swLegends.keys())], \
              [label for i,label in enumerate(labels) if i in display]+[swLegends[x][1] for x in sorted(swLegends.keys())], \
              loc='upper left', fontsize=16, ncol=1)
    ax.grid()
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)

    # plt.savefig('%s.png' % (dataF), bbox_inches='tight')
    # plt.savefig('%s.png' % ('scaledCPU'), bbox_inches='tight')
    plt.savefig(fig_name, format=fig_name.split('.')[-1], dpi=300, bbox_inches='tight')




    # f_cap_x = range(0, 101, 10)
#    f_cap_x = range(0, 100*nCores, 5*nCores)
#    f_cap_y = p(f_cap_x)

#    print '%s:%s (%f)' % (dataF.split('-')[0].replace('AT', '@'), f_cap, p(95*nCores))

    # print ' '.join(map(str, f_cap_x)
    # print ' '.join(map(str, f_cap_y))

#    fig = plt.figure()
#    ax = fig.add_subplot(1,1,1)
#    swLegends = {}
#    color = colors.next()
#    for nsw in sorted(cpu.keys()):
#        m = marker.next()
#        # ax.plot(cpu[nsw], thput[nsw], linestyle = '', marker=m, c=color, markersize=8) #, xp, p30(xp), '--') , label='%s switches' % nsw
#        ax.plot(scaledCPU[nsw], thput[nsw], linestyle = '', marker=m, c=color, markersize=8) 
        # Create custom artists
#        if m == '*':
#            l = plt.Line2D((0,1),(0,0), color='w', marker=m, linestyle='', markersize=10)
#        else:
#            l = plt.Line2D((0,1),(0,0), color='w', marker=m, linestyle='', markersize=8)
#        if nsw not in swLegends:
#            swLegends[int(nsw)] = [l, '%d-switch' % (int(nsw)-2)]

#    label = '%s-%s' % (dataF.split('-')[0].replace('AT', '@'), dataF.split('-')[1])
#    label = dataF.split('-')[0].replace('AT', '@')
#    ax.plot(f_cap_x, f_cap_y, linestyle = '-', c=color, linewidth=3, label=label)


#    plt.xlabel('CPU Usage (%)', fontsize=18)
#    plt.ylabel('Total Throughput (%s)' % thputType, fontsize=18)
    # plt.ylim(0, 2000)
#    plt.ylim(0, param[thputType]['ylim'])

#plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
#Get artists and labels for legend and chose which ones to display
#handles, labels = ax.get_legend_handles_labels()
#display = range(len(dataFiles)) # (0,1,2)

# ax.legend(loc='upper left', fontsize=12)
#Create legend from custom artist/label lists
#ax.legend([handle for i,handle in enumerate(handles) if i in display]+[swLegends[x][0] for x in sorted(swLegends.keys())], \
#          [label for i,label in enumerate(labels) if i in display]+[swLegends[x][1] for x in sorted(swLegends.keys())], \
#          loc='upper left', fontsize=16, ncol=1)
#ax.grid()
#plt.xticks(fontsize=18)
#plt.yticks(fontsize=18)

# plt.savefig('%s.png' % (dataF), bbox_inches='tight')
# plt.savefig('%s.png' % ('scaledCPU'), bbox_inches='tight')
#plt.savefig('%s.eps' % ('scaledCPU'), format='eps', dpi=300, bbox_inches='tight')

def main():

    parser = argparse.ArgumentParser(description='Compute and plot capacity function from resource quantification experiments')

    parser.add_argument('-d', '--data-files',
                        dest='data_files',
                        action='store',
                        type=str,
                        required=True,
                        help='Data file of resoure quantification experiments',
    )

    parser.add_argument('-f', '--figure',
                        dest='fig',
                        action='store',
                        type=str,
                        default='cpu-plot.png',
#                        required=True,
                        help='Capacity function plot: filename.[eps|png]',
    )

    parser.add_argument('-t', '--throughput-type',
                        dest='thput_type',
                        action='store',
                        type=str,
                        default='pps',
#                        required=True,
                        help='Throughput type for capacity function:pps,mbps',
    )

    args = parser.parse_args()
    dataFs = args.data_files.split(',')
    cpu_info, thput_info, pm_cores = parseData(dataFs, args.thput_type)
    capfs = capFuncRegression(cpu_info, thput_info)
    plotCapfs(capfs, cpu_info, thput_info, pm_cores, dataFs, args.thput_type, args.fig)


if __name__ == '__main__':
    main()
