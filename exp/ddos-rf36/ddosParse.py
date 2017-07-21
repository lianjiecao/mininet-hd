import sys, subprocess, argparse
import numpy as np

# os.path.isfile(fname) 
mapAlg = {'UC':'UC-MKL', 'US':'Share-METIS', 'METIS':'Equal-METIS', 'OVER':'OVER-PROV', 'MN':'SwitchBinPlacer', 'GROUND':'OVER-PROV', \
    'WF':'Waterfall', 'VOID':'Waterfall', 'C90':'$C_i(0.9)$', 'MAX_CPU':'MAX_CPU', 'MAX_CPU_N':'MAX_CPU_N'}
# {'cap34', 1357, 'cap31', 1357, 'cap32', 796, 'cap35', 558, 'cap33', 558, 'cap36', 321}
# pms = {'cap34':'PM1', 'cap31':'PM2', 'cap32':'PM3', 'cap35':'PM4', 'cap33':'PM5', 'cap36':'PM6'}
pms = {'PM1':'cap34', 'PM2':'cap31', 'PM3':'cap32', 'PM4':'cap35', 'PM5':'cap33', 'PM6':'cap36'}


def updateList(infoList, infoSample):
    for key in infoSample:
        infoList.setdefault(key, []).append(infoSample[key])
    return


def parseCPUIntf(fileName):
    bw = fileName.split('-')[2][:2]
    f = open(fileName, 'r')
    lines = f.read().strip().split('\n')
    intfThput = {}
    cpu = {}
    pmThput = {}
    sw2pm = {}

    for line in lines:
        if line.startswith('cap'):
            tokens = line.split()
            pm = tokens[0].split('-')[0]
            sw = tokens[0].split('-')[1]
            sw2pm.setdefault(pm, set()).add(sw)
            if 's' in tokens[0]:
                intfThput.setdefault(pm, {})
                intfThput[pm][tokens[0]] = [float(x)/float(bw) for x in tokens[20:100]]
            elif 'cpu' in tokens[0]:
                cpu[tokens[0]] = [float(x)/100 for x in tokens[20:100]]

    tmpThput = {}
    for pm in intfThput:
        tmpThput[pm] = []
        for intf in intfThput[pm]:
            tmpThput[pm].extend(intfThput[pm][intf])

    for pm in intfThput:
        for s in intfThput[pm]:
            if sum(intfThput[pm][s]) != 0:
                pmThput.setdefault(pm, {})
                pmThput[pm][s] = sum(intfThput[pm][s]) / len(intfThput[pm][s])


    ### Print Link utilization ###
    print 'link%s %s %s' % ( fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], \
        ' '.join(['%.4f' % np.mean(tmpThput[pms[x]]) for x in sorted(pms.keys()) if pms[x] in pmThput.keys()]) )
    print 'linkErr%s %s %s' % ( fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], \
        ' '.join(['%.4f' % np.std(tmpThput[pms[x]]) for x in sorted(pms.keys()) if pms[x] in pmThput.keys()]) )

    ### Print CPU utilization ###
    print 'cpu%s %s %s' % ( fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], \
        ' '.join(['%.4f' % np.mean(cpu[pms[x]+'-cpu']) for x in sorted(pms.keys())]))
    print 'cpuErr%s %s %s' % ( fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], \
        ' '.join(['%.4f' % np.std(cpu[pms[x]+'-cpu']) for x in sorted(pms.keys())]))

    # print 'cpu'+fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], ' '.join(['%.4f' % np.mean(cpu[pms[x]+'-cpu']) \
    #     for x in sorted(pms.keys())])
    # print 'cpuErr'+fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], ' '.join(['%.4f' % np.std(cpu[pms[x]+'-cpu']) \
    #     for x in sorted(pms.keys())])

    f.close()


def parseHTTP(fileName, httpTarget):

    ret = subprocess.check_output("grep i-dflt %s | awk '{print $4}'" % fileName, shell=True)
    httpThput = [float(x) / httpTarget for x in ret.split()[:-5]]
    print 'http%s %s %s' % ( fileName.split('-')[1].upper(), mapAlg[fileName.split('-')[3]], ' '.join(['%.4f' % x for x in httpThput]) )


def main():
    parser = argparse.ArgumentParser(description="Parse DDoS experiment results")

    parser.add_argument('--output-dir',
                        dest="dir",
                        action="store",
                        help="Output directory",
                        type=str,
                        default='./',
                        )

    parser.add_argument('--http-target',
                        dest="httpTarget",
                        action="store",
                        help="The target HTTP request rate",
                        type=int,
                        default=300,
                        )

    args = parser.parse_args()
    parseCPUIntf('%s/parsed-intfs-cpu.log' % args.dir)
    parseHTTP('%s/pg-server-console.out' % args.dir, args.httpTarget)


if __name__ == '__main__':
    main()
