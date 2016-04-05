import re, argparse, subprocess


parser = argparse.ArgumentParser(description="Parse RocketFuel topologies")
parser.add_argument('-f',
                    dest="file",
                    action="store",
                    required=False,
                    help="File name")

parser.add_argument('-d',
                    dest="dir",
                    action="store",
                    required=False,
                    help="directory name")

args = parser.parse_args()


def checkUnconnected_dfs(v, checked):
    if v in verts:
        checked.add(v)
        for vName in verts[v]['nb']:
            if vName not in checked:
                checkUnconnected_dfs(vName, checked)
        return


if args.file:
    files = [args.file]
if args.dir:
    files = subprocess.check_output('ls -t '+args.dir+'*.r0.cch', shell=True).split()

for fname in files:
    numBB = 0
    print fname.split('/')[-1]
    f = open(fname, 'r')
    entries = f.read().split('\n')
    verts = {}
    for e in entries:
        if '+ bb' in e:
            numBB = numBB + 1
        match = re.search('<.*>', e)
        if match:
            if '+ bb' in e:
                verts[e.split(' ')[0]] = {'bb':'bb', 'nb':re.sub('<|>', '', match.group()).split()}
            else:
                verts[e.split(' ')[0]] = {'bb':'nbb', 'nb':re.sub('<|>', '', match.group()).split()}
            
    s = set()
    checkUnconnected_dfs(entries[0].split()[0], s)

    print len(s), len(verts), '\n'
    fw = open(fname+'.abr','w')
    for r in s:
        fw.write(r+' '+verts[r]['bb']+' '+' '.join(verts[r]['nb'])+'\n')
    fw.close()
